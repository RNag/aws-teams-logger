from contextlib import nullcontext as does_not_raise

import pytest

from aws_teams_logger import LambdaLogger
from aws_teams_logger.loggers.globals import Globals


@pytest.fixture(autouse=True)
def reset_env(record_env_changes):
    # Call test function
    yield
    # Teardown
    LambdaLogger.reset_validation_state()
    Globals.reset()


def test_validate_vars_with_parameters():
    with pytest.raises(ValueError):
        ll = LambdaLogger()
        ll()

    with does_not_raise():
        LambdaLogger(ses_identity='my@identity.test',
                     teams_email='my@teams.email')
        ll()

    # The :attr:`_VALIDATED` will be true on Base Logger, so
    # expect the validation to not happen again.
    with does_not_raise():
        ll = LambdaLogger()
        ll()


def test_validate_vars_with_env():

    with pytest.raises(ValueError):
        ll = LambdaLogger(ses_identity='my@identity.test')
        ll()
