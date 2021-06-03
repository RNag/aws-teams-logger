"""
Common test fixtures and additional config for `pytest`
"""
import importlib
import os
from dataclasses import dataclass
from unittest import mock
from uuid import uuid4

import aws_teams_logger.constants as lc
import aws_teams_logger.loggers.base_logger as bl

import pytest


# Default AWS profile - update if needed
DEFAULT_PROFILE = 'my-aws-profile'

# AWS Account Alias that will included in email messages
AWS_ACCOUNT_NAME = 'my-test-account-alias'

# SES Identity, must be verified from the SES console
SES_IDENTITY = 'replace-me@email.com'

# Teams Email for test cases (sends notifications to a test channel)
TEAMS_EMAIL = 'abc123.domain.com@amer.teams.ms'

# Comma-separated list of Dev Emails to notify, will be used in test cases
# where exceptions are raised
DEV_EMAILS = 'replace-me@email.com'


@pytest.fixture(scope='module')
def record_env_changes():
    """Record any changes to the environment; needed since these variables are cached"""
    reload_modules()


def reload_modules():
    """Need to reload modules to record changes to the env variables"""
    for module in lc, bl:
        importlib.reload(module)


@pytest.fixture(scope='module')
def mock_env():
    """Mocks environment variables for a test case"""
    env_var_to_value = {
        'AWS_PROFILE': os.getenv('AWS_PROFILE', DEFAULT_PROFILE),
        'AWS_ACCOUNT_NAME': AWS_ACCOUNT_NAME,
        'SES_IDENTITY': SES_IDENTITY,
        'TEAMS_EMAIL': TEAMS_EMAIL,
        'DEV_EMAILS': DEV_EMAILS,
    }

    with mock.patch.dict(os.environ, env_var_to_value):
        reload_modules()
        yield


@pytest.fixture(scope='module')
def request_id():
    """
    Returns a random UUID similar to an AWS Request ID. The UUID is unique to
    the test suite, so all test cases in a single run should share the Request ID.
    """
    return str(uuid4())


@dataclass
class TestsWithMarkSkipper:
    """
    Util to skip tests with mark, unless cli option provided.
    """

    test_mark: str
    cli_option_name: str
    cli_option_help: str

    def pytest_addoption_hook(self, parser):
        parser.addoption(
            self.cli_option_name,
            action='store_true',
            default=False,
            help=self.cli_option_help,
        )

    def pytest_runtest_setup(self, item):
        if self.test_mark in item.keywords and not item.config.getoption(self.cli_option_name):
            self._skip_test()

    def _skip_test(self):
        reason = 'need {} option to run this test'.format(self.cli_option_name)
        pytest.skip(reason)


mutative_skipper = TestsWithMarkSkipper(
    test_mark='mutative',
    cli_option_name="--run-all",
    cli_option_help="run all test cases, including any potentially destructive tests",
)

pytest_addoption = mutative_skipper.pytest_addoption_hook
pytest_runtest_setup = mutative_skipper.pytest_runtest_setup
