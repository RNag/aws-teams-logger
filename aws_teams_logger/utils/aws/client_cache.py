from collections import defaultdict

from boto3 import Session, client
from botocore.client import BaseClient
from botocore.exceptions import UnknownServiceError


class ClientCache:

    # boto3 service name
    SERVICE_NAME = None

    # sub-classes can specify that client objects should be thread-safe
    THREAD_SAFE = False

    _clients = defaultdict(dict)

    def __init__(self, region_name='us-east-1', profile_name=None,
                 init_client=False):
        """Initializes a :class:`ClientCache` object.

        `region_name` is the specified region that is bound to a client,
        which defaults to "us-east-1".

        `init_client` will automatically initialize the client for the region,
        and is useful when service requests will be made in multiple threads and
        it is desirable to reuse the same client between threads.

        """
        self.region_name = region_name.lower()
        self.profile_name = profile_name

        if init_client:
            _ = self.client

    @property
    def client(self):
        return self._get_client(self.region_name)

    @client.setter
    def client(self, value):
        raise Exception('Member read-only')

    def _get_client(self, region_name):
        """
        Internal method to return a low-level SecretManager client for a given region name
        """
        if region_name not in self._clients[self.SERVICE_NAME]:
            self._clients[self.SERVICE_NAME][region_name] = self._create_client()

        return self._clients[self.SERVICE_NAME][region_name]

    def _create_client(self) -> BaseClient:
        if not self.SERVICE_NAME:
            raise ValueError(
                'Sub-classes must provide a value for "SERVICE_NAME"')

        try:
            if self.THREAD_SAFE or self.profile_name:
                client_func = Session(profile_name=self.profile_name).client
            else:
                client_func = client
            return client_func(self.SERVICE_NAME, self.region_name)

        except UnknownServiceError:
            raise NotImplementedError(
                'Sub-classes must override this method')
