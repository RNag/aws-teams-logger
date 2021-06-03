"""
Models for the 'Logger' decorator classes

"""
__all__ = ['LambdaContext', 'TaskContext', '_BaseContext']

import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Any

import requests

from .log import LOG


@dataclass
class _BaseContext:
    """
    Base Context class, which defines the minimum attributes that a Context
    object would be expected to contain.
    """
    function_name: str


class TaskContext(_BaseContext):

    def __init__(self, fn: Callable):
        """
        Create a :class:`TaskContext` object.
        """
        super().__init__(fn.__qualname__)

    @classmethod
    def get_ecs_metadata(cls, endpoint_env_var='ECS_CONTAINER_METADATA_URI_V4'
                         ) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for the ECS or Fargate task, if available.
        Uses the Task Metadata V4 endpoint.

        Ref: https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html
        """
        metadata_url = os.getenv(endpoint_env_var)

        if not metadata_url:
            docs_link = ('https://docs.aws.amazon.com/AmazonECS/latest/userguide/'
                         'task-metadata-endpoint-v4-fargate.html')
            LOG.info(
                f'Environment variable "{endpoint_env_var}" not defined '
                'in task; consider updating to platform version 1.4.0 to enable '
                'this feature. Please refer to the following docs:\n'
                f'  {docs_link}')
            return

        return cls._retrieve_ecs_metadata(metadata_url)

    @staticmethod
    def _retrieve_ecs_metadata(metadata_url: str) -> Dict[str, Any]:
        """
        Make a call to the ECS Metadata endpoint and return the result as a
        dictionary object.
        """
        r = requests.get(metadata_url)
        r.raise_for_status()

        return r.json()


class LambdaContext(_BaseContext):

    def __init__(self, function_name: str,
                 request_id=None, account_id=None, account_name=None):
        """
        Create a :class:`LambdaContext` object.
        """
        super().__init__(function_name)

        self.request_id = request_id
        self.account_id = account_id
        self.account_name = account_name
