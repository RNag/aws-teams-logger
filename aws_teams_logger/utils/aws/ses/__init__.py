"""
High-level implementation of the boto3 library for SES

Read the Docs here:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html

"""

__all__ = ['SESHelper', 'BulkDestination']


from .ses import SESHelper
from .models import *
