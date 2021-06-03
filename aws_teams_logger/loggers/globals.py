__all__ = ['Globals', 'set_account_name']

from dataclasses import dataclass
from typing import Optional


_EMPTY_VALUES = (None, '')


@dataclass
class __Globals:
    """
    Global defaults
    """

    # Minimum log level for messages sent to Teams
    enabled_lvl: str = 'WARNING'

    # Outbound SES identity
    ses_identity: Optional[str] = None

    # MS Teams email
    teams_email: Optional[str] = None

    # Optional dev emails to notify, when a lambda fails
    dev_emails: Optional[str] = None

    # AWS Account Name (alias)
    account_name: Optional[str] = None

    def __setattr__(self, key, value):
        if value not in _EMPTY_VALUES:
            super().__setattr__(key, value)

    def reset(self):
        """Resets all attributes in the instance."""
        new_obj = self.__class__()
        self.__dict__ = new_obj.__dict__


# Define a singleton instance so we can go through our custom `__setattr__`
Globals = __Globals()


def set_account_name(account_name: str):
    """Convenience function to set the AWS account alias (name)"""
    Globals.account_name = account_name
