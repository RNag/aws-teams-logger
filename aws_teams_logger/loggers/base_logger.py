import functools
import logging
import logging.config
import sys
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from typing import Optional, Tuple, Dict, DefaultDict, Any, List, Callable, Union

import boto3
from botocore.exceptions import ClientError

from .globals import Globals
from ..constants import *
from ..log import LOG, setup_logging, original_log_method
from ..models import _BaseContext
from ..utils.aws.ses import SESHelper, BulkDestination
from ..utils.date_util import local_now
from ..utils.decorators import log_time
from ..utils.types import get_formatted_message


class _BaseLogger(ABC):

    # Prefix string for the 'subject' used in email messages
    SUBJECT_PREFIX = 'FAILURE'

    # The type or classification of the decorated function
    #
    # For example, 'Lambda' indicates an AWS Lambda function.
    FUNCTION_TYPE = 'Base'

    # Checks whether required vars are validated (either defined in environment
    # or passed in as parameters). This should only be run once for all
    # decorated functions.
    #
    # Note: don't directly modify this value; use `reset_validation_state` to
    # reset this attribute if needed.
    _VALIDATED = False

    def __init__(self, f: Optional[Callable] = None, *,
                 enabled_lvl: Optional[str] = None,
                 ses_identity: Optional[str] = None,
                 teams_email: Optional[str] = None,
                 dev_emails: Optional[str] = None,
                 logger_cls=logging.Logger,
                 log_func_name='_log',
                 raise_=True):
        """
        Create and return a :class:`_BaseLogger` object.

        This defines a decorator method which handles the posting of warning
        level or above log messages (used via the builtin ``logging`` module)
        to a specified Microsoft Teams channel. Log messages with an `exc_info`,
        as well as any uncaught exceptions, will also be sent to an optional
        list of Developer Emails via Microsoft Outlook.

        This is an abstract class and should not be used directly. Instead,
        please import the concrete sub-classes which implement all required
        methods in this containing class:

            * :class:`LambdaLogger` - The main use case is to decorate a handler for
              a Python lambda function. For decorating multiple lambda handlers,
              it is useful to invoke the helper method `decorate_all_functions`.

            * :class:`TaskLogger` - Intended to be used with ECS functions, such as
              functions that will be run in a Fargate task. However this can also
              be used to decorate any generic functions as well.

            * :class:`BulkLambdaLogger`, :class:`BulkTaskLogger` - The decorator
              classes prefixed with `Bulk` are functionally identical to their
              above counterparts, but prefer to send emails in bulk where
              possible. As such, emails are sent in batches once each decorated
              function has completed execution. See the below section on **Bulk
              Loggers** for more info.

        The following environment variables will be used if provided:

            * `AWS_ACCOUNT_NAME` - AWS Account Alias (name); if defined, will
              be used instead of making a call to `iam:ListAccountAliases`
              to retrieve the alias of the current AWS account.

            * `TEAMS_LOG_LVL` - Can be used instead of the ``enabled_lvl``
              parameter. This determines the minimum log level for messages
              sent to Teams. The default value is 'WARNING', which means
              that log messages at the 'WARNING', 'ERROR', and 'EXCEPTION'
              levels will be sent to Teams, but not messages at the 'INFO'
              or 'DEBUG' level.

            * `TEAMS_EMAIL` - The email to send log messages or lambda failures
              (e.g. uncaught exceptions) to. Required, if not passed in via the
              constructor.

            * `SES_IDENTITY` - Sender or outbound email, must be validated under
              SES in the AWS console. Required, if not passed in via the
              constructor.

            * `DEV_EMAILS` - Comma delimited list of dev emails, if provided
              will send stylized HTML to them when any uncaught exceptions are
              raised. Example: 'user1@my.domain.org,user2@my.domain.org'

            * `SOURCE_CODE` - A link to the source code repo (such as Bitbucket)
               for the project.

            * `AWS_LOG_GROUP` - Only applies when the `TaskLogger` decorator is
              used. Determines the log group to link to in the AWS console.
              Generally this is not needed to be specified (see note on 'ECS
              Tasks' below)

            * `AWS_REGION` - AWS Region, should be automatically set for AWS
              Lambda functions. Determines the region in which to invoke the SES
              service, as well as the default region for Lambda and Task
              contexts. Example: 'us-east-1'

            * `LOG_CFG` - If specified, sets up logging via `logging.basicConfig`.
              Also determines the minimum level at which messages logged by this
              library show up in CloudWatch. If this is a valid path to a file,
              the contents will be passed to `logging.config.dictConfig` instead.
              Example: 'INFO'

            * `LOCAL_TZ` - User's local time zone, passed in to ``pytz.timezone``;
              used when generating the date/time in the subject for a Teams or
              Devs email message (Example: 'US/Eastern')

        The `logger_cls` and `log_func_name` together determine the base log
        function to decorate. By default we decorate the `logging.Logger._log`
        method, which is the base method used by all logger methods.

        The constructor also accepts an optional `enabled_lvl` parameter, which
        determines the minimum log level (ex. "ERROR") at which messages are
        logged to Teams, but the preferred option is to globally set the
        environment variable 'TEAMS_LOG_LVL', as this will also work better
        when the decorating multiple lambda handlers in a module.


        Simple Usage:

            >>> from aws_teams_logger import LambdaLogger

            >>> log = logging.getLogger(__name__)

            >>> @LambdaLogger
            >>> def my_lambda_handler(event: Dict[str, Any], context: Any):
                >>> ...
                >>> other_func()
                >>> ...

            >>> def other_func():
                # Message is not logged to Teams (default log level is "WARN")
                >>> log.info('Info level log')
                # This message will be forwarded to Teams
                >>> log.warning('Sample Warn message')
                # Messages with the `exc_info` parameter will be logged to both
                # the Teams Channel and any subscribed Dev Emails via Outlook
                >>> try:
                    >>> empty_dict = {}
                    >>> value = empty_dict['missing key']
                >>> except KeyError:
                    >>> log.error('Key missing from `empty_dict`', exc_info=True)
                # Uncaught errors will be logged to both Teams and any Dev Emails
                >>> finally:
                    >>> result = 1 / 0

        For ECS Tasks:

            The decorator retrieves ECS metadata on the currently running task
            when posting messages to Teams or via email. It will automatically
            retrieve data from the Task Metadata V4 endpoint, if this is
            available. To enable correct data reporting for the the V4 endpoint,
            set the `Platform Version` for the task to "1.4.0" or higher as
            mentioned in the article below.

            https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html


            Usage for Tasks:

                >>> from aws_teams_logger import TaskLogger

                >>> log = logging.getLogger(__name__)

                >>> class MyTaskClass:
                    >>>
                    >>> @classmethod
                    >>> @TaskLogger
                    >>> def my_task_func(cls, *args, **kwargs):
                        >>> ...
                        >>> cls.other_func()
                        >>> ...
                    >>>
                    >>> @staticmethod
                    >>> def other_func():
                        # See logging example under "Simple Usage" section above
                        >>> ...

        Bulk Loggers:

            The `Bulk` logger implementations will send templated emails in bulk,
            e.g. via the ``ses:SendBulkTemplatedEmail`` API call. Use this
            implementation when it is expected that multiple logs will be sent to Teams
            or Outlook, as there will be a performance increase when using a `Bulk`
            logger.


            Sample Usage for Bulk Loggers:

                >>> from aws_teams_logger import BulkLambdaLogger

                >>> log = logging.getLogger()

                >>> @BulkLambdaLogger
                >>> def my_lambda_handler(event: Dict[str, Any], context: Any):
                    >>> log.info("This %s message shouldn't be logged", 'Info')
                    >>> for i in range(5):
                        >>> log.error('Testing %d ...', i + 1)
                    >>> ...

        """
        # Copy over global defaults
        Globals.ses_identity = ses_identity
        Globals.teams_email = teams_email
        Globals.dev_emails = dev_emails
        # Setup logging config
        setup_logging()

        self._func = f
        self.enabled_lvl = self._get_enabled_lvl(enabled_lvl)
        self.logger_cls = logger_cls
        self.log_func_name = log_func_name
        self.raise_ = raise_
        # Update wrapper function, if needed
        functools.update_wrapper(self, self._func)
        # noinspection PyTypeChecker
        # This property will be set by the sub-classes.
        self.context: _BaseContext = None

    def __call__(self, *param_args, **param_kwargs):
        """
        Decorates (wraps) function `f` to to stream log messages at the
        `enabled_lvl` or above, as well as any uncaught exceptions, to the
        specified Teams channel.

        Also optionally sends any errors to a comma-separated list of
        'DEVS_EMAIL', if this value is defined.

        """
        # Validate any required vars here, so we don't run into errors later
        # when the emails need to be sent.
        self._validate_vars_if_needed()

        def decorator(func):
            @functools.wraps(func)
            def new_func(*args, **kwargs):
                # Set context object
                self._set_context(func, *args, **kwargs)
                # Run optional setup method
                self._setup_func()

                try:
                    # Call decorated function and return the result
                    return func(*args, **kwargs)

                except Exception as e:
                    if hasattr(e, 'code') and hasattr(e, 'message'):
                        # Exceptions with :attr:`code` and :attr:`message` in our case
                        # should already be logged to Teams
                        LOG.error('Failure, err_code=%s, err_msg=%s',
                                  e.code, e.message, exc_info=e)

                    else:
                        LOG.error('Failure: %s', str(e), exc_info=e)
                        # Send lambda failure to Teams
                        self._send_to_ses(error=self._format_exception(e))

                    if self.raise_:
                        raise

                finally:
                    # Run optional teardown method
                    self._teardown_func()

            return new_func

        # We're called without parens - ex. @DecoratorClass
        if self._func:
            return decorator(self._func)(*param_args, **param_kwargs)

        # We're called with parens - ex. @DecoratorClass(key='value')
        # In this case, the only argument will be the function to decorate.
        try:
            func = param_args[0]
        except IndexError:
            # Normally this won't happen, if the decorator is used properly
            return decorator

        return decorator(func)

    def __get__(self, instance, owner):
        """
        Fix: make our decorator class a decorator, so that it also works to
        decorate instance methods.

        https://stackoverflow.com/a/30105234/10237506
        """
        from functools import partial
        return partial(self.__call__, instance)

    def _setup_func(self):
        """Setup runs *before* the decorated function is called."""

        # Get original (e.g. un-decorated) log method
        log_method = original_log_method(self.logger_cls, self.log_func_name)
        # Decorate log method - needs to be inside the decorator to avoid
        # potential bugs when multiple decorated functions are run.
        setattr(self.logger_cls, self.log_func_name,
                self._decorate_log_method(log_method))

    def _teardown_func(self):
        """Teardown runs *after* the decorated function finishes running."""
        pass

    @property
    def ses(self):
        return SESHelper(AWS_REGION)

    @property
    def ses_identity(self):
        return SES_IDENTITY or Globals.ses_identity

    @property
    def teams_email(self):
        return TEAMS_EMAIL or Globals.teams_email

    @property
    def dev_emails(self):
        return DEV_EMAILS or Globals.dev_emails

    @staticmethod
    def reset_validation_state():
        """
        Used to clear :attr:`_VALIDATED` in case we need to re-validate when
        the :meth:`__call__` decorator is run again.
        """
        _BaseLogger._VALIDATED = False

    @classmethod
    def _get_account_name(cls):
        """
        Retrieve the human-readable account name to show in logs for a given
        AWS Account ID.

        If an env variable 'AWS_ACCOUNT_NAME' is defined, this value will
        be used instead.

        Note: Lambdas and ECS tasks must otherwise have the necessary
        permissions (shown below) for this call to be successful. If not,
        the account name won't be resolved and an error will be logged to
        CloudWatch.

            {
                "Effect": "Allow",
                "Action": "iam:ListAccountAliases",
                "Resource": "*"
            }

        """

        def get_account_alias(default_alias='Unknown') -> str:
            """Retrieve account name from environment, or IAM if undefined."""

            # Short path: check if the account alias is defined in environment
            if AWS_ACCOUNT_NAME:
                return AWS_ACCOUNT_NAME

            # Retrieve the alias from an `iam:ListAccountAliases` API call
            try:
                @log_time(log_message='Retrieved the AWS account alias from IAM')
                def get_account_alias_from_iam():
                    return boto3.client('iam').list_account_aliases()['AccountAliases'][0]

                return get_account_alias_from_iam()

            except Exception as e:
                LOG.error('Unable to retrieve the account alias, please ensure '
                          'the attached role has the necessary permissions '
                          '(iam:ListAccountAliases). Error: %s', e)

                return default_alias

        if not Globals.account_name:
            Globals.account_name = get_account_alias()

        return Globals.account_name

    @abstractmethod
    def _set_context(self, func, *args, **kwargs):
        """
        Set the context object, for example a Lambda Context object.

        An implementation should set the :attr:`context` object which can extend
        from the :class:`_BaseContext` class.
        """

    @abstractmethod
    def _get_context_and_links(self) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
        """
        Return a two-tuple of (context_data, links)

        `context_data` is a dictionary containing key:value pairs to show in a
        Teams message, and `links` is a list of dictionary objects each
        containing a "location" and "text" field.
        """

    def _get_subject(self, dt_format='%m/%d/%Y %I:%M%p') -> str:
        """
        Generate a subject for the Teams or Devs email message.

        Uses the class attribute `SUBJECT_PREFIX` which can optionally be set.
        """
        dt_now = local_now().strftime(dt_format)
        return f'{self.SUBJECT_PREFIX}: {self.context.function_name}, {dt_now}'

    def _validate_vars_if_needed(self):
        if _BaseLogger._VALIDATED:
            return

        if not self.ses_identity:
            raise ValueError(
                'SES Identity must be set, either as an argument to the '
                'constructor or via the "SES_IDENTITY" environment variable.')

        if not self.teams_email:
            raise ValueError(
                'MS Teams Email (ex: abc123.my.domain@amer.teams.ms) must be '
                'set, either as an argument to the constructor or via the '
                '"TEAMS_EMAIL" environment variable.')

        _BaseLogger._VALIDATED = True

    @staticmethod
    def _get_enabled_lvl(enabled_lvl: Optional[str] = None) -> int:
        """
        Get enabled log level, e.g. minimum log level to stream messages to Teams
        """
        default_enabled_log_lvl = enabled_lvl or Globals.enabled_lvl
        return logging._nameToLevel[TEAMS_LOG_LVL or default_enabled_log_lvl]

    def _decorate_log_method(self, f):
        """
        Decorate (wrap) the specified base log method.

        By default, decorates the base method func:`Logger._log` from the
        `logging` library.
        """
        @functools.wraps(f)
        def new_log_func(self_: logging.Logger, level, msg, msg_args,
                         exc_info=None, *args, **kwargs):

            if level >= self.enabled_lvl:
                send_kwargs = {'msg': get_formatted_message(msg, msg_args),
                               'lvl': level}
                if exc_info:
                    send_kwargs['error'] = self._format_exception(exc_info)

                self._send_to_ses(**send_kwargs)

            return f(self_, level, msg, msg_args,
                     exc_info=exc_info, *args, **kwargs)

        return new_log_func

    @staticmethod
    def _format_exception(exc_info):
        """
        Format `exc_info` or current exception info as a tuple of
        (type, value, traceback).

        Copied from the ``logging`` module for now.

        """
        if isinstance(exc_info, BaseException):
            return type(exc_info), exc_info, exc_info.__traceback__
        elif not isinstance(exc_info, tuple):
            return sys.exc_info()
        return exc_info

    @classmethod
    def _get_msg_with_exc_trace(cls, exc_info, msg: Optional[str] = None):
        """
        Get error message with the error traceback included.
        Copied directly from the ``logging`` module for now.

        TODO: Perhaps update to decorate `Logger.handle` method instead,
            that way we can get the formatted `exc_info` directly.
        """
        def _format_exc_traceback(ei) -> str:
            sio = StringIO()
            tb = ei[2]
            traceback.print_exception(ei[0], ei[1], tb, None, sio)
            s = sio.getvalue()
            sio.close()
            if s[-1:] == '\n':
                s = s[:-1]
            return s

        if exc_info:
            exc_info = cls._format_exception(exc_info)
            exc_text = _format_exc_traceback(exc_info)
            if exc_text:
                return f'{msg.strip()}\n\n{exc_text}' if msg else exc_text

        return msg

    def _send_to_ses(self, *, msg: Optional[str] = None, lvl: Optional[str] = None,
                     error=None):
        """
        Forwards a log message `msg` logged at `lvl` or an exception `error` to
        the Teams channel

        This method accepts keyword arguments only, to avoid any confusion.

        If uncaught exceptions were raised in the decorated handler and env
        variable `DEV_EMAILS` is provided, send out a specially formatted email
        to those users as well.

        """
        subject = self._get_subject()
        context, links = self._get_context_and_links()

        send_data = {'subject': subject,
                     'context': context,
                     'message': msg,
                     'links': links}
        if error:
            self._notify_dev_emails()

            error_msg_with_tb = self._get_msg_with_exc_trace(error, msg)

            if lvl:
                lvl_name = logging._levelToName.get(lvl, logging.ERROR)
                error_msg_with_tb = f'[{lvl_name.upper()}] {error_msg_with_tb}'
                send_data['level'] = lvl_name.capitalize()

            send_data['error'] = {
                'class': error[0].__name__,
                'message': getattr(error[1], 'message', error_msg_with_tb)
            }

        self._send_templated_email('send-to-teams', send_data, self.teams_email)

    def _notify_dev_emails(self):
        """
        Notifies any devs about an error, if needed
        """
        if not self.dev_emails:
            return

        subject = self._get_subject()
        context, links = self._get_context_and_links()

        context_data = context.copy()

        # Retrieve account info
        account_data = {}
        for key in 'Account Name', 'Account Id':
            value = context_data.pop(key, None)
            if value:
                account_data[key] = value

        # Commenting this out for now - would be nice to use, but
        # it's specific to Python 3.8 and above.
        # account_data = {k: v for k in ('Account Name', 'Account Id')
        #                 if (v := context_data.pop(k, None))}

        send_outlook_data = {'subject': subject,
                             'function_type': self.FUNCTION_TYPE,
                             'context': context_data,
                             'account': account_data,
                             'links': links}

        self._send_templated_email(
            'send-to-outlook', send_outlook_data, self.dev_emails)

    def _send_templated_email(self, name: str,
                              data: Dict[str, Any],
                              to_addresses: Union[List[str], str]):
        """
        Sends a templated email using SES. If an error occurs, log a message if
        the error is a known one, otherwise raise the original error.

        :param name: Name of the SES template
        :param data: Template data as a dictionary object
        :param to_addresses: List of recipients for the email
        """
        try:
            self.ses.send_templated_email(name, data, to_addresses,
                                          self.ses_identity, self.ses_identity)

        except ClientError as ce:
            self._handle_send_template_err(name, ce)

    @staticmethod
    def _handle_send_template_err(name: str, ce: ClientError):
        """Handles errors when sending an email via the SES service"""
        error = ce.response.get('Error', {})
        error_code = error.get('Code', 'Unknown')

        if error_code == 'TemplateDoesNotExist':
            LOG.error(
                f'Template {name} does not exist; please call '
                f'`upload_templates` to upload the required SES templates.')
        else:
            raise


class _BulkBaseLogger(_BaseLogger, ABC):
    """
    This is an abstract class that can improve application performance (when
    several logs are involved) by sending templated emails in bulk.

    See the documentation in the base class (:class:`_BaseLogger`) for more
    info.

    """
    def __init__(self, f: Optional[Callable] = None, **kwargs):
        super().__init__(f, **kwargs)
        self._template_to_dest: DefaultDict[
            str, List[BulkDestination]] = defaultdict(list)

    def _send_templated_email(self, name: str,
                              data: Dict[str, Any],
                              to_addresses: Union[List[str], str]):
        """
        Overrides the method which sends an individual email via SES to instead
        add it to the list of emails to send in a `batch` once the decorated
        function completes.
        """
        destination = BulkDestination(data, to_addresses)
        self._template_to_dest[name].append(destination)

    def _teardown_func(self):
        """Teardown runs *after* the decorated function finishes running."""

        if self._template_to_dest:
            # AWS recommends instantiating the client, and then passing
            # them to any sub-threads
            _ = self.ses.client

            num_workers = min(len(self._template_to_dest), 3)

            # Sends bulk emails to Teams and Outlook in parallel
            with ThreadPoolExecutor(max_workers=num_workers) as pool:
                for name, dest in self._template_to_dest.items():
                    pool.submit(self._send_bulk_templated_email, name, dest)

            # Clear the list of emails to send
            self._template_to_dest.clear()

    def _send_bulk_templated_email(self, name: str,
                                   destinations: List[BulkDestination]):
        """
        Sends a bulk templated email using SES. If an error occurs, log a
        message if the error is a known one, otherwise raise the original error.

        :param name: Name of the SES template
        :param destinations: List of email destinations, each with individual
          template data
        """
        try:
            self.ses.send_bulk_templated_email(
                name, destinations,
                self.ses_identity, self.ses_identity)

        except ClientError as ce:
            self._handle_send_template_err(name, ce)
