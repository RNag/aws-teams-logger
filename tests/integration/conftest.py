from unittest.mock import Mock

import pytest


@pytest.fixture(scope='module', autouse=True)
def setup_env(mock_env):
    """Setup the mock environment for all test cases in the module."""
    pass


@pytest.fixture
def mock_context(request, request_id):
    """
    Build and return a mock lambda context
    """
    return get_mock_context(request.function, request_id)


def get_mock_context(func, request_id: str,
                     account_id=123456789,
                     log_group_name='my-test-group',
                     log_stream_name='my-test-stream'):
    """
    Return a mock lambda context for a given function `func`
    """
    func_name = func.__qualname__
    func_parts = func_name.split('.')
    # Fix for cases where we have a function within a function,
    #   e.g. TestClass.some_test_method.<locals>.f2
    if len(func_parts) > 2 and 'locals' in func_parts[-2]:
        func_name = f'{func_parts[-3]}.{func_parts[-1]}'

    return Mock(function_name=func_name, aws_request_id=request_id,
                log_group_name=log_group_name, log_stream_name=log_stream_name,
                invoked_function_arn=f'a:b:c:d:{account_id}')
