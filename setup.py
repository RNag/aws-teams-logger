import pathlib

from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent

package_name = 'aws_teams_logger'

packages = find_packages(exclude=['tests.*', 'tests'])

requires = [
    'pytz>=2018.1,<2022.0',
    'requests'
]

test_requirements = [
    'pytest-cov',
    'pytest-mock',
    'pytest>=6,<7'
]

about = {}
exec((here / package_name / '__version__.py').read_text(), about)

readme = (here / 'README.md').read_text()

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={package_name: package_name},
    include_package_data=True,
    install_requires=requires,
    license=about['__license__'],
    # download_url='https://github.com/user/reponame/archive/v_01.tar.gz',
    keywords=['teams logger', 'ms-teams-logger',
              'microsoft teams', 'ms-teams',
              'teams logger for AWS',
              'aws-lambda', 'ecs', 'fargate'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: System :: Logging',
        'Topic :: Communications :: Chat',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.7',
    tests_require=test_requirements,
    extras_require={
        'standalone': ['boto3~=1.17.85']
    }
)
