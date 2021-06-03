"""
Remove a list of email templates from SES
"""
from aws_teams_logger.log import LOG
from .utils import get_templates, setup_logging
from ..ses import SESHelper


def delete_templates(profile_name=None):
    setup_logging()
    ses = SESHelper(profile_name=profile_name)

    templates = [template.name for template in get_templates()]

    LOG.info('Attempting to delete %d templates...', len(templates))

    for template in templates:
        LOG.info('[ %s ]', template)
        success = ses.delete_template(template)
        if success:
            LOG.info('Deleted')
        else:
            LOG.error('There was an issue deleting the template')
