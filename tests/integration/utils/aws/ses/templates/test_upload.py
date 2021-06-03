import pytest

from aws_teams_logger import upload_templates, delete_templates


@pytest.mark.mutative
def test_upload_templates(mock_env):
    """Upload SES templates to the specified AWS account"""
    upload_templates()


@pytest.mark.mutative
def test_delete_templates(mock_env):
    """Delete SES templates from the specified AWS account"""
    delete_templates()
