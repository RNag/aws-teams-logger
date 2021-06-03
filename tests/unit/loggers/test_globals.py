import pytest

from aws_teams_logger.loggers.globals import Globals, set_account_name


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset the `Globals` object after each test case"""
    yield Globals
    # teardown
    Globals.reset()


def test_enabled_lvl_is_updated():
    assert Globals.enabled_lvl == 'WARNING'
    for lvl_to_set in (' ', 'testing'):
        Globals.enabled_lvl = lvl_to_set
        assert Globals.enabled_lvl == lvl_to_set


def test_enabled_lvl_is_not_updated():
    assert Globals.enabled_lvl == 'WARNING'
    for lvl_to_set in ('', None):
        Globals.enabled_lvl = lvl_to_set
        assert Globals.enabled_lvl != lvl_to_set
        assert Globals.enabled_lvl == 'WARNING'


def test_reset():
    expected_identity = 'my-identity.test'
    expected_teams_email = 'my-email.org'
    expected_account_name = 'my-aws-account'

    Globals.teams_email = expected_teams_email
    Globals.ses_identity = expected_identity
    set_account_name(expected_account_name)

    assert Globals.teams_email == expected_teams_email
    assert Globals.ses_identity == expected_identity
    assert Globals.account_name == expected_account_name

    Globals.reset()

    # Confirm all attributes are reset to their defaults
    assert Globals.teams_email is None
    assert Globals.ses_identity is None
    assert Globals.account_name is None
