# AWS Teams Logger

AWS Teams Logger is a Python library that forwards errors (failures) and log
messages to a MS Teams channel, and an optional list of *Developer Emails*
who may need to be notified; the emails use HTML formatting which is
originally designed for MS Outlook and Teams. This library is primarily intended
for use in an AWS environment.

This package exposes the below decorator classes which handle the posting
of **warning** level or above log messages by default (via the builtin `logging` module)
to a specified Microsoft Teams channel. Log messages with an `exc_info` parameter,
as well as any uncaught exceptions, will also be sent to a list of Dev Emails (if provided)
in addition to being logged to the Teams channel.

**Available Decorators**:

  * `LambdaLogger` - The main use case is to decorate a handler for
    an AWS Lambda function in the Python runtime. For decorating multiple lambda handlers,
    it is useful to invoke the helper method `decorate_all_functions`.
    

  * `TaskLogger` - Intended to be run in ECS environment, such as
    functions (or class methods) that are run in an ECS or Fargate task.
    However, this can also be used to decorate any generic functions as well.
    Note that the task needs to be using *platform version 1.4* 
    (see the [note below](#note-on-ecs-tasks) for more details)


  * `BulkLambdaLogger`, `BulkTaskLogger` - The decorator classes that start with *Bulk*
    are functionally identical to their above counterparts, but prefer to send emails in bulk where
    possible. Use this implementation when it is expected that multiple logs will be sent to Teams
    or Outlook, as there will be a performance increase with a *Bulk*
    logger.
    See the below section on [Bulk Loggers](#bulk-loggers) for more info.

## Usage

Simple Usage for a stand-alone AWS Lambda function:

```python3
from aws_teams_logger import LambdaLogger
from logging import getLogger
from typing import Dict, Any

log = getLogger(__name__)
log.setLevel('INFO')

# By default, only logs from this library at the 'WARNING' level and above
# should show up in CloudWatch. This specifies the minimum log level at which
# library logs appear in CloudWatch.
# getLogger('aws_teams_logger').setLevel('INFO')

# Note: this is a simplified example, and assumes you define the required
# environment variables. Otherwise, you'd need to pass the parameters
# to the decorator class like `@LambdaLogger(teams_email='my-teams-email')
# in this case.

@LambdaLogger
def my_lambda_handler(event: Dict[str, Any], context: Any):
    ...
    other_func()
    ...

def other_func():
    # Message is not logged to Teams (default log level is "WARN")
    log.info('Info level log')
    # This message will be forwarded to Teams
    log.warning('Sample Warn message')
    # Messages with the `exc_info` parameter will be logged to both
    # the Teams Channel and any subscribed Dev Emails via Outlook
    try:
        empty_dict = {}
        value = empty_dict['missing key']
    except KeyError:
        log.error('Key missing from `empty_dict`', exc_info=True)
    # Uncaught errors will be logged to both Teams and any Dev Emails
    finally:
        result = 1 / 0
```

... or for a module with multiple handlers, common for serverless projects with
    multiple Lambdas:

```python3
from aws_teams_logger import LambdaLogger
from logging import getLogger

log = getLogger()
ll = LambdaLogger(enabled_lvl='WARNING')

def my_handler_1(event, context):
    # This message won't be sent to Teams, as the minimum lvl here is 'WARNING'
    log.info('Hello world!')
    # Build a custom Exception object - a `ValueError` in this case -
    # which will be forwarded to Teams and also any Devs via email
    err = ValueError('My sample error details.')
    log.error('This is an error log with a sample exception object', exc_info=err)

def my_handler_2(event, context):
    # This message will be sent to Teams by default, though this behavior
    # can be overridden via the 'enabled_lvl' parameter above, or alternatively
    # via the 'TEAMS_LOG_LVL' environment variable defined for the lambda.
    log.warning('Help! something went wrong')

# Now, decorate all the lambda handlers declared above
ll.decorate_all_functions(ses_identity='my@identity.org',
                          teams_email='abc123.my.domain@amer.teams.ms',
                          dev_emails='user1@my.domain.org,user2@mydomain.org')
```

... or use it to decorate one or more ECS tasks:

```python3
import logging
from aws_teams_logger import TaskLogger

log = logging.getLogger(__name__)

# Logs from this library won't show up by default. This will enable reporting
# of logs above a specified level. You can alternatively define the 'LOG_CFG'
# environment variable, which does the same thing.
logging.basicConfig(level='WARNING')

class MyTaskClass:

    @classmethod
    @TaskLogger
    def my_task_func(cls, *args, **kwargs):
        ...
        cls.other_func()
        ...

    @staticmethod
    def other_func():
        # TODO add logic here; see examples for logging above
        ...
```

... when multiple emails will be sent using the same template,
it might be more performant to use a Bulk Logger as shown below:

```python3
from aws_teams_logger import BulkLambdaLogger
from logging import getLogger

log = getLogger()

@BulkLambdaLogger
def my_lambda_handler(event, context):
    log.info("This %s message shouldn't be sent via email", 'Info')
    for i in range(5):
        log.error('Testing %d ...', i + 1)
    ...
```

## Installing Teams Logger and Supported Versions

AWS Teams Logger is available on PyPI:

```shell
pip install aws-teams-logger
```

This package officially supports **Python 3.7** or higher.

## About

This library decorates (overrides) the base logger methods in the `logging` module to also
post log messages above a set level to a Teams channel.

The library also posts to target destinations via email currently; it doesn't currently
support Teams connectors. It uses [Amazon SES](https://aws.amazon.com/ses/details/)
to  format the error and log messages that will be sent to MS Teams and Outlook.
Therefore, you will first need to set up SES and allow permissions for the
decorated function to send emails via the SES service, as explained below.

### Conditional Dependencies

Note that `boto3` is not included in package requirements by default,
since an AWS Lambda environment is assumed.

If running on a Docker environment such as ECS or Fargate, you
can use the following to ensure that all dependencies are installed:

```shell
pip install aws-teams-logger[standalone]
```

## Initial Setup

### SES

#### Add Required Templates

The library uses SES templates to format email messages sent to MS Teams and Outlook.

Use the below helper function to add the required templates to the desired AWS account:

```python
from aws_teams_logger import upload_templates


upload_templates(profile_name='my-aws-profile')
```

#### Set up an SES Identity

Add and verify an identity from the Amazon SES console under your
account. For testing purposes, it might be preferable to use a personal email address
as it'll be easier to verify it.

#### Turn off Sandbox Mode

Enable _Production Access_ from the SES console. This will enable
us to send outbound emails without needing to verify each recipient email
separately.

### Teams

Use the steps below to find the email address for the MS teams channel to stream
the logs to:

1. Click on the _three dots_ to the right of the channel name
2. Select 'Get email address'
3. Here we only need to use the email address.

   For example, given `Channel name <abc123.my.domain@amer.teams.ms>`
   we only need the value that is enclosed in brackets.

## Permissions

The execution IAM role will need the following minimum permissions:

```json
[
    {
        "Effect": "Allow",
        "Action": [
            "ses:Send*Email"
        ], 
        "Resource": "*"
    }, 
  
    {
        "Effect": "Allow", 
        "Action": "iam:ListAccountAliases", 
        "Resource": "*"
    }
]
```

Note that if you set the AWS account name (either via the `set_account_name` function or
the `AWS_ACCOUNT_NAME` environment variable) then you don't need to add the second
permission to retrieve the account alias from IAM.

Example of setting the AWS account name:
```python
from aws_teams_logger import set_account_name


set_account_name('my-account-alias')
```

## Required Values

The library requires certain values that need to either be passed in as parameters to the decorators
(or alternatively to the `decorate_all_functions` method for lambda functions),
or which need to be present in the environment.

The following minimum values are required to use the decorator methods (otherwise
it should log an error):

* _SES Identity_ - Sender email address that was previously validated with SES.
* _MS Teams Email_ - The email address (ex: abc123.my.domain@amer.teams.ms) to send
  log messages and unhandled errors to.

## Parameters

The resolution logic for parameters will use the environment variables
first if they are available.


The following table lists the parameter names as used with the decorators,
along with the environment variables that will be used if provided.
Note that the resolution order is from left to right.

| Env Variable | Parameter | Example | Description |
| --- | --- | --- | --- |
| `SES_IDENTITY` | `ses_identity` | sender@my.domain.org | Sender or outbound email, must be validated in the SES console |
| `TEAMS_EMAIL` | `teams_email` | abc123.my.domain@amer.teams.ms | The email to send log messages or failures (e.g. uncaught exceptions) to |
| `TEAMS_LOG_LVL` | `enabled_lvl` | WARNING | The minimum log level for messages sent to Teams |
| `DEV_EMAILS` | `dev_emails` | user1@my.domain.org,user2@my.domain.org | Comma delimited list of dev emails, if provided will send stylized HTML to them when any uncaught exceptions are raised |
| `AWS_ACCOUNT_NAME` | `set_account_name()` | my-account-dev | AWS Account Alias. If defined, will be used instead of making a call to `iam:ListAccountAliases` to retrieve the alias of the current AWS account. |
| `SOURCE_CODE` | - | https://github.com/abc/repo | A link to the source code repo (such as Bitbucket) for the project. |
| `AWS_LOG_GROUP` | - | my-cw-log-group | Only applies when the `TaskLogger` decorator is used. Determines the log group to link to in the AWS console. Generally this is not needed to be specified (see note on 'ECS Tasks' below) |
| `AWS_REGION` | - | us-east-1 | AWS Region, should be automatically set for AWS Lambda functions. Determines the region in which to invoke the SES service, as well as the default region for Lambda and Task contexts. |
| `LOG_CFG` | - | INFO | If specified, sets up logging via `logging.basicConfig`. Also determines the minimum level at which messages logged by this library show up in CloudWatch. If this is a valid path to a file, the contents will be passed to `logging.config.dictConfig` instead. 
| `LOCAL_TZ` | - | US/Eastern | User's local time zone, passed in to `pytz.timezone`; used when generating the date/time in the subject for a Teams or Devs email message.

### Advanced Config

The decorator parameters `logger_cls` and `log_func_name` together determine the base log
function to decorate.

By default, we decorate the `logging.Logger._log`
method, which is the base method used by all logger methods in the Python `logging` library.

## Note on ECS Tasks

The decorator retrieves ECS metadata on the currently running task
when posting messages to Teams or via email. It will automatically
retrieve data from the Task Metadata V4 endpoint, if this is
available.

To enable correct data reporting for the the V4 endpoint,
set the `Platform Version` for the task to **1.4.0** or higher as
mentioned in the article below.

https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html

## Bulk Loggers

The _Bulk_ logger implementations will send templated emails in bulk,
e.g. via the ``ses:SendBulkTemplatedEmail`` API call. Use this
implementation when it is expected that multiple logs will be sent via
the same SES template, as there will be a performance increase when using a _Bulk_
logger. Note that there is a separate template for
sending a message to Teams and Outlook. 

Please see the tests under the [perf_tests/](./tests/integration/perf_tests) directory for a
performance comparison between the _Individual_ (default) vs _Bulk_ Loggers.

### Considerations
Some important considerations when choosing a *Bulk* Logger:

* As we want to bulk send emails where possible, emails are sent in batches once each decorated
  function returns.
* Because emails are sent in bulk, it's expected that the messages will be out of order.
For example, a message logged at the end of a decorated function might show up earlier than
  a message logged at the start of the function.
  * As a general rule, use the time listed on the `subject` header in the Teams message; this is the time
    at when the message was originally logged. Note that this might not always align with
  timestamp that Teams lists for when the message was delivered.

## Common Issues
This section describes common errors that might show up, along with the steps to resolve them.

### Template Not Found

#### Example
```
aws_teams_logger - ERROR - Template [send-to-teams | send-to-outlook] does not exist; please call `upload_templates` to upload the required SES templates.
```

#### Resolution

As mentioned, you will need to call the `upload_templates` function to
add the required SES templates to the AWS account.

```python
from aws_teams_logger import upload_templates

upload_templates(profile_name='my-aws-profile')
```

Expected output:
```
aws_teams_logger - INFO - [ send-to-teams ]
aws_teams_logger - INFO - Uploading SES template...
aws_teams_logger - DEBUG - send-to-teams: creating template, as it does not exist
aws_teams_logger - INFO -   SUCCESS
aws_teams_logger - INFO - [ send-to-outlook ]
aws_teams_logger - INFO - Uploading SES template...
aws_teams_logger - DEBUG - send-to-outlook: creating template, as it does not exist
aws_teams_logger - INFO -   SUCCESS
```

### Unable to Send Email

#### Example
```
An error occurred (AccessDenied) when calling the SendTemplatedEmail operation: User `arn:aws:iam::1234567890:user/my-user' is not authorized to perform `ses:SendTemplatedEmail' on resource `arn:aws:ses:us-east-1:1234567890:identity/sender@my.domain.org'
```

#### Resolution

Update the attached IAM role to allow the `ses:SendTemplatedEmail` action as discussed above.


### Unable to Determine Account Name

#### Example
```
aws_teams_logger - ERROR - Unable to retrieve the account alias, please ensure the attached role has the necessary permissions (iam:ListAccountAliases). Error: An error occurred (AccessDenied) when calling the ListAccountAliases operation: User: arn:aws:iam::1234567890:user/my-user is not authorized to perform: iam:ListAccountAliases on resource: *
```

#### Resolution

Update the attached IAM role to allow the `iam:ListAccountAliases` action as discussed above.

You can also set the `AWS_ACCOUNT_NAME` environment variable or call `set_account_name()`, and this will eliminate
the need of an API call made to IAM to retrieve the alias of the current account.
