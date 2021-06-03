Release History
===============

dev
---

-   \[Short description of non-trivial change.\]

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
