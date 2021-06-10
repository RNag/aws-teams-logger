# -*- coding: utf-8 -*-

"""
MS Teams / Email Logger for AWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AWS Teams Logger is a Python library that forwards errors (failures) and log
messages to a MS Teams channel and an optional list of Developer Emails who may
need to be notified -- adds HTML formatting originally designed for MS Outlook.

Simple Usage for an AWS Lambda function:

    >>> from aws_teams_logger import LambdaLogger
    >>> from logging import getLogger
    >>>
    >>> log = getLogger()
    >>>
    >>> # Note: this is a simplified example, and assumes you define the required
    >>> # environment variables. Otherwise, you'd need to pass the parameters
    >>> # to the decorator class like `@LambdaLogger(teams_email='my-teams-email')
    >>> # in this case.
    >>>
    >>> @LambdaLogger
    >>> def my_lambda_handler(event, context):
    >>>   # This message can be sent to Teams, depending on the enabled log lvl
    >>>   log.info('Hello world!')
    >>>   try:
    >>>     result = 1 / 0
    >>>   except ZeroDivisionError:
    >>>     # This will forward the error to Teams, and notify any Devs via email
    >>>     log.error('Unable to divide by zero', exc_info=True)
    >>>     # Be sure not to re-raise the exception as below, as that will log
    >>>     # a duplicate message to Teams and Outlook
    >>>     # raise


Please see the docs for additional examples and some important how-to's.

"""
__all__ = [
    'LambdaLogger',
    'TaskLogger',
    'BulkLambdaLogger',
    'BulkTaskLogger',
    'set_account_name',
    'upload_templates',
    'delete_templates'
]

import logging

from .loggers import *
from .utils.aws.ses.templates import *

# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger('aws_teams_logger').addHandler(logging.NullHandler())
