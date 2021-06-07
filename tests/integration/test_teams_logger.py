from logging import getLogger

import pytest

from aws_teams_logger.loggers import LambdaLogger, TaskLogger
from .conftest import get_mock_context


log = getLogger(__name__)


def test_basic_log_to_teams(mock_context):
    """
    Simple logging to teams
    """

    @LambdaLogger(enabled_lvl='INFO', raise_=False)
    def lambda_handler(_event, _context):
        log.info('%s log', 'Info')
        # Should not be logged to teams, but will show in console logs
        log.debug('Debug log')

    lambda_handler(None, mock_context)


def test_basic_log_to_teams_without_parens(mock_context):
    """
    Simple logging to teams, when decorator is called w/o parens
    """

    @LambdaLogger
    def lambda_handler(_event, _context):
        # Should not be logged to teams, but will show in console logs
        log.info('%s log', 'Info')
        # will be logged to Teams (default level is WARNING)
        log.warning('Warning log')

    lambda_handler(None, mock_context)


def test_basic_log_to_teams_with_exc_info(mock_context):
    """
    Confirm messages are properly formatted and logged to teams and outlook
    when the `exc_info` parameter is passed.
    """

    @LambdaLogger
    def lambda_handler(_event, _context):
        # Log messages with a custom :class:`Exception` object should be
        # forwarded to both Teams and any subscribed Dev Emails.
        err = ValueError('My sample error details.')
        log.error('This is a sample error log', exc_info=err)

        try:
            1 / 0
        except ZeroDivisionError as e:
            # Should not be logged to teams, but will show in console logs
            log.info('%s log', 'Info', exc_info=e)
            # will be logged to Teams and Outlook (default level is WARNING)
            log.warning('Warning log', exc_info=e)
            log.error('Error log', exc_info=True)

    lambda_handler(None, mock_context)


def test_log_to_teams_with_errors(mock_context):
    """
    Confirm messages are logged to teams when uncaught exceptions are raised.
    """

    @LambdaLogger(enabled_lvl='ERROR', raise_=False)
    def my_func(_context):
        log.error('Error log')
        # Should not be logged to teams, but will show in console logs
        log.warning('Warning log')

        # Raises an index error
        my_list = []
        _value = my_list[1]

    my_func(mock_context)


def test_log_to_teams_with_multiple_lambdas(request_id):
    """
    Test case to demonstrate intended operation of the `LambdaLogger` when
    decorating and calling more than one function.

    In this example, the log methods in the `logging` module are decorated
    twice, before each of the decorated functions run. This ensures the
    enabled log level for each decorator is correctly applied when the
    function runs.

    Note: While this way also works, the suggested way for a module with
    multiple lambda handlers is to use environment variables. Thus, in CFN
    template we can specify the corresponding env variable (e.g. TEAMS_LOG_LVL)
    for each lambda.

    """

    @LambdaLogger(enabled_lvl='INFO')
    def f1(_context):
        log.info('info message')
        log.warning('warning message')

    @LambdaLogger(enabled_lvl='ERROR')
    def f2(_context):
        log.warning('warning message')
        log.error('error message')

    ctx_f1 = get_mock_context(f1, request_id)
    ctx_f2 = get_mock_context(f2, request_id)

    f1(ctx_f1)
    f2(ctx_f2)


def test_log_to_teams_with_multiple_tasks():
    """
    Test case to demonstrate intended operation of the `TaskLogger` when
    decorating and calling more than one function.

    In this example, the log methods in the `logging` module are decorated
    twice, before each of the decorated functions run. This ensures the
    enabled log level for each decorator is correctly applied when the
    function runs.

    This should send out a total of 3 notifications to MS Teams, as well as
    a notification to :attr:`DEV_TEST_EMAIL` if defined, as an exception is
    raised in the second task.

    """

    class FirstTask:
        @classmethod
        @TaskLogger(enabled_lvl='WARNING')
        def run(cls):
            log.info('info message')
            log.warning('warning message')

    class SecondTask:
        @classmethod
        @TaskLogger(enabled_lvl='ERROR')
        def run(cls):
            log.warning('warning message')
            log.error('error message')
            d = {}
            # Should result in a KeyError being raised
            _ = d['my-key']

    FirstTask.run()
    with pytest.raises(KeyError):
        SecondTask.run()


def test_decorate_all_functions():
    """
    Please note: the `decorate_all_functions` call is not expected to
    work in cases such as these, where we have nested functions (e.g.
    functions within functions). This is because modifying the outer
    function locals (e.g. `locals()`) is not expected to work in
    Python, and so any inner functions remain unchanged even after
    modification of the locals object.

    I have also tested passing the functions directly to the decorator
    method, e.g. creating a `decorate_functions` method and passing in
    `f1` as an argument to the method which should wrap the local function.
    However the function `f1` remains unchanged even after this approach,
    so this test case will be a no-op for now. For clarification, the
    `decorate_all_functions` method should work perfectly fine when
    decorating all the top-level functions in a module.

    See the below docs for more info:
    https://stackoverflow.com/questions/37600997/python-locals-update-not-working

    """
    ll = LambdaLogger()

    def f1(_context):
        log.info('info message')
        log.warning('warning message')

    def f2(_context):
        log.warning('warning message')
        log.error('error message')

    id_f1 = id(f1)
    id_f2 = id(f2)

    # Decorate function `f2` using the LambdaLogger object
    f2 = ll(f2)

    assert id_f2 != id(f2), "Decorator did not modify function `f2`"

    try:
        ll.decorate_all_functions()
    except KeyError:
        # We'd expect a KeyError to be raised because function locals
        # doesn't contain a __name__ as we're making the call within
        # a function (but in global scope, `locals` is same as `globals`)
        pass

    assert id_f1 == id(f1), "`decorate_all_functions` modified " \
                            "function `f1`, so we're all good!"
