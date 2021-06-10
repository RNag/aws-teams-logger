import inspect
import os
from json import dumps
from logging import basicConfig, getLogger
from typing import Optional, List

from aws_teams_logger.log import LOG


template_file = 'template.py'
exclude_dirs = ('__pycache__', )

module_name = os.path.splitext(template_file)[0]


def setup_logging():
    basicConfig(level='INFO')
    # Turn down the `botocore` libraries
    getLogger('botocore').setLevel('WARNING')


def get_templates() -> List['TemplateBuilder']:
    """Return all SES templates within the current directory"""
    import importlib

    templates = []
    script_dir = os.path.abspath(os.path.dirname(__file__))
    split_pos = 5
    base_package = '.'.join(script_dir.rsplit('/', split_pos)[-split_pos:])

    tree = os.walk(script_dir, topdown=True)

    for root, dirs, files in tree:
        for dir in exclude_dirs:
            dir in dirs and dirs.remove(dir)

        if root == script_dir:
            continue

        if template_file not in files:
            continue

        package_name = root.split('/')[-1].replace('/', '.')
        module_path = f'{base_package}.{package_name}.{module_name}'

        try:
            template = importlib.import_module(module_path)
        except ModuleNotFoundError:
            LOG.warning(f"Unable to import '{module_path}'")
            continue

        template_data: TemplateBuilder = getattr(template, 'data')
        templates.append(template_data)

    return templates


class TemplateBuilder:
    """
    Class to construct the necessary parameters used to update
    an SES template.

    """
    def __init__(self, name: str, subject: str,
                 html_body: Optional[str] = None):
        self.name = name
        self.subject = subject
        if html_body:
            self.html_contents = html_body
        else:
            caller_dir = os.path.dirname((inspect.stack()[1])[1])
            self.html_contents = self.read_html_contents(caller_dir)

    @staticmethod
    def read_html_contents(path: str, html_file_path='body.html'):
        html_file = os.path.join(path, html_file_path)
        return open(html_file).read()

    def dict(self):
        template_data = {
            "TemplateName": self.name,
            "SubjectPart": self.subject,
            "HtmlPart": self.html_contents
        }

        return template_data

    def __str__(self):
        return dumps(self.dict())
