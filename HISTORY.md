Release History
===============

dev
---

-   \[Short description of non-trivial change.\]

0.4.0 (2021-06-07)
------------------

**Features and Improvements**
-   Log messages that contain an `exc_info` parameter should
    now be sent to both Teams and any subscribed Dev emails.
    The messages also be properly formatted with the exception
    traceback info (thanks to the `logging` module)

**Important Notes**
-   The SES template `send-to-teams` has been updated;
    it's recommended that users update the SES template via a
    `upload_templates` call.

0.3.0 (2021-06-03)
------------------

**Features and Improvements**
-   Add a global function `set_account_name` which can be used to set the AWS account name, 
    which will eliminate the need of an IAM call to retrieve the account alias.

0.2.0 (2021-06-03)
------------------

**Features**
-   Allow the local timezone to be configured via the `LOCAL_TZ` environment variable

**Bugfixes**
-   The class decorators should now correctly work both when called with and w/o parentheses
