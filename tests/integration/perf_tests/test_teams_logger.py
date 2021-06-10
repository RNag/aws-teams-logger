import cProfile
from logging import getLogger

import pytest

from aws_teams_logger import *


log = getLogger(__name__)


@pytest.fixture
def num_emails():
    """Increase / decrease this value as needed"""
    return 20


@pytest.fixture
def profiler(request):
    # setup
    pr = cProfile.Profile()
    pr.enable()
    # call test function
    yield
    # teardown
    pr.disable()
    print('{div} Profile for: {name} {div}'.format(
        div='=' * 5, name=request.function.__qualname__))
    pr.print_stats(sort='time')


@pytest.mark.long
def test_individual_logger(mock_env, profiler, num_emails):

    class MyTaskClass1:
        @TaskLogger
        def __call__(self, *args, **kwargs):
            log.info("This %s message shouldn't be logged", 'Info')
            for i in range(num_emails):
                err = ValueError(f'Sample Error {i + 1}')
                # This should send an email to both Teams and Outlook
                log.error('INDIVIDUAL Test %d ...', i + 1,
                          exc_info=err)

    MyTaskClass1()()


@pytest.mark.long
def test_bulk_logger(mock_env, profiler, num_emails):

    class MyTaskClass2:
        @BulkTaskLogger
        def __call__(self, *args, **kwargs):
            log.info("This %s message shouldn't be logged", 'Info')
            for i in range(num_emails):
                err = ValueError(f'Sample Error {i + 1}')
                # This should send an email to both Teams and Outlook
                log.error('BULK Test %d ...', i + 1,
                          exc_info=err)

    MyTaskClass2()()
