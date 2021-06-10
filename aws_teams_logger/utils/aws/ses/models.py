__all__ = ['BulkDestination']

from json import dumps
from typing import NamedTuple, Union, List, Dict, Any

from ...types import as_list


class BulkDestination(NamedTuple):
    """
    Specifies a single entry in the `Destinations` parameter of an
    ``ses:SendBulkTemplatedEmail`` operation.

    Ref:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html#SES.Client.send_bulk_templated_email

    """
    # The replacement template data
    data: Dict[str, Any]

    # A list of recipients for the email
    to_addresses: Union[List[str], str]

    @property
    def dict(self):
        """
        Return an entry that can be added to the `Destinations` list in a
        request to the ``ses:SendBulkTemplatedEmail`` API.
        """
        return {
            'Destination': {
                # We can similarly add any 'CcAddresses' and 'BccAddresses'
                # here, if needed.
                'ToAddresses': as_list(self.to_addresses)
            },
            'ReplacementTemplateData': dumps(self.data)
        }
