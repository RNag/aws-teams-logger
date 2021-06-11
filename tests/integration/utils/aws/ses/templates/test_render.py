import pytest

from aws_teams_logger.utils.aws.ses import SESHelper


@pytest.fixture(scope='module')
def ses(mock_env):
    return SESHelper()


@pytest.mark.skip('Because it opens a new browser tab')
def test_render_send_to_teams(ses):
    """Test rendering the `send-to-teams` SES template"""
    ses.test_render_template('send-to-teams', {
        'subject': 'LAMBDA INFO: test_basic_log_to_teams, 06/11/2021 10:40AM',
        'color': '#FF0000',
        'level': 'WARNING',
        'error': {'class': 'Test', 'message': 'My\nMessage\nHere'}})
