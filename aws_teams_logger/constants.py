import os

__all__ = ['LOG_LEVEL', 'AWS_ACCOUNT_NAME',
           'TEAMS_LOG_LVL', 'TEAMS_EMAIL',
           'SES_IDENTITY', 'DEV_EMAILS',
           'SOURCE_CODE', 'AWS_LOG_GROUP',
           'LOCAL_TZ']


# Minimum level for logs to CloudWatch
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

# AWS Account Alias (name), can be optionally set in the environment
#
# If defined, will be used instead of making a call to `iam:ListAccountAliases`
# to retrieve the alias of the current AWS account.
AWS_ACCOUNT_NAME = os.getenv('AWS_ACCOUNT_NAME')

# Minimum log level for messages sent to Teams
TEAMS_LOG_LVL = os.getenv('TEAMS_LOG_LVL')

# MS Teams email
TEAMS_EMAIL = os.getenv('TEAMS_EMAIL')

# SES outbound email address
SES_IDENTITY = os.getenv('SES_IDENTITY')

# Comma delimited field, if provided will send stylized HTML to them
#
# Example:
#   'user1@my.domain.org,user2@my.domain.org'
DEV_EMAILS = os.getenv('DEV_EMAILS')

# Optional link to source code repo for the project
SOURCE_CODE = os.getenv('SOURCE_CODE')

# (ECS Tasks) Optional link to the AWS log group
AWS_LOG_GROUP = os.getenv('AWS_LOG_GROUP')

# Local time zone
LOCAL_TZ = os.getenv('LOCAL_TZ', 'US/Eastern')
