from aws_teams_logger.log import LOG
from .utils import get_templates, setup_logging
from ..ses import SESHelper


def upload_templates(profile_name=None):
    """
    Upload templates to SES, updating any existing templates if necessary.

    Walks through all packages under the current directory. If the package
    contains a :attr:`template_file` which defines a `data` attribute
    representing the template data, it replaces the template on SES with
    the current version on the local.

    """
    setup_logging()
    ses = SESHelper(profile_name=profile_name)

    for template in get_templates():

        LOG.info('[ %s ]', template.name)
        LOG.info(f'Uploading SES template...')
        success = ses.replace_template(template.dict())
        if success:
            LOG.info('  SUCCESS')
        else:
            LOG.warning('  FAILED')
