import inspect
from typing import Dict, Any, List, Tuple, Optional

from .base_logger import _BaseLogger, _BulkBaseLogger
from .globals import Globals
from ..constants import AWS_REGION, SOURCE_CODE
from ..log import LOG
from ..models import LambdaContext


class LambdaLogger(_BaseLogger):
    """
    This class can be used to decorate a handler for a Python lambda function.

    For decorating multiple lambda handlers, it is useful to use the method
    `decorate_all_functions`.

    See the documentation in the base class (:class:`_BaseLogger`) for more
    info.

    """
    SUBJECT_PREFIX = 'LAMBDA FAILURE'

    FUNCTION_TYPE = 'Lambda'

    _decorated = []

    def decorate_all_functions(self, enabled_lvl: Optional[str] = None,
                               ses_identity: Optional[str] = None,
                               teams_email: Optional[str] = None,
                               dev_emails: Optional[str] = None):
        """
        Decorates all functions (assumed to be lambda functions) in the calling
        module with the wrapper provided by :class:`LambdaLogger`

        See documentation under the constructor for :class:`_BaseLogger`
        (e.g. `BaseLogger()`) for info on parameters.

        This method call is ideally made after all desired functions to be
        decorated are implemented in the caller module. See below for an
        example.


        module_a.py:

            def f1():   # This function will be decorated
                ...

            def f2():   # This is also decorated
                ...

            LambdaLogger().decorate_all_functions(teams_email='abc123.my.domain@amer.teams.ms')

            def f3():   # This function won't be decorated as it's defined later
                ...

        """
        # Copy over global defaults
        Globals.enabled_lvl = enabled_lvl
        Globals.ses_identity = ses_identity
        Globals.teams_email = teams_email
        Globals.dev_emails = dev_emails

        caller = inspect.stack()[1]
        caller_module_locals = caller[0].f_locals
        caller_module_name = caller_module_locals['__name__']

        # Decorate all functions in module
        decorated_functions = []
        for attr, fn in caller_module_locals.items():
            if self._should_decorate_fn(caller_module_name, fn):
                # Decorate the function if its local to the caller module
                caller_module_locals[attr] = self.__call__(fn)
                decorated_functions.append(attr)

        LOG.debug(
            'Successfully decorated %d lambda functions: %s',
            len(decorated_functions), decorated_functions)

    @classmethod
    def _should_decorate_fn(cls, module_name: str, fn: Any) -> bool:
        """
        Confirm that a function is defined in the module and has not been
        previously decorated.

        Return a boolean indicating whether the function should be decorated.
        """
        if not callable(fn) or fn.__module__ != module_name:
            return False

        key = f'{module_name}.{fn.__name__}'

        if key in cls._decorated:
            return False

        cls._decorated.append(key)
        return True

    def _set_context(self, func, *args, **kwargs):
        try:
            # Context is generally passed as 2nd argument for lambda functions,
            # but to be safe we use the last positional argument instead.
            self.context = args[-1]
        except IndexError:
            # Not a regular lambda function - perhaps a local function used
            # for testing purposes.
            self.context: Any = LambdaContext(func.__name__)

    def _get_context_and_links(self) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
        links = []
        aws_root = 'https://console.aws.amazon.com'

        if isinstance(self.context, LambdaContext):
            # Mock lambda context (lambda function has an empty or missing
            # context argument)
            return {'Function Name': self.context.function_name}, links

        log_group_name = self.context.log_group_name
        log_stream_name = self.context.log_stream_name

        account_id = self.context.invoked_function_arn.split(':')[4]
        account_name = self._get_account_name()

        context = {'Function Name': self.context.function_name,
                   'Request Id': self.context.aws_request_id,
                   'Account Name': account_name,
                   'Account Id': account_id}

        if SOURCE_CODE:
            links.append({'location': SOURCE_CODE, 'text': 'Link to Source'})

        links.append({
            'location': f'{aws_root}/lambda/home?region={AWS_REGION}#/'
                        f'functions/{self.context.function_name}',
            'text': 'Link to Lambda'
        })

        links.append({
            'location': f'{aws_root}/cloudwatch/home?region={AWS_REGION}#logEventViewer:'
                        f'group={log_group_name};stream={log_stream_name}',
            'text': 'Link to Logs'
        })

        return context, links


class BulkLambdaLogger(LambdaLogger, _BulkBaseLogger):
    """
    This class can be used to decorate a handler for a Python lambda function.

    The `Bulk` logger implementation will send templated emails in bulk,
    e.g. via the ``ses:SendBulkTemplatedEmail`` API call. Use this
    implementation when it is expected that multiple logs will be sent to Teams
    or Outlook, as there will be a performance increase when using a `Bulk`
    logger.

    For decorating multiple lambda handlers, it is useful to use the method
    `decorate_all_functions`.

    See the documentation in the base class (:class:`_BaseLogger`) for more
    info.

    """
