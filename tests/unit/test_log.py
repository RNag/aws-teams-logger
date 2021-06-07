from aws_teams_logger.log import original_log_method


def test_original_log_method():
    """
    Test case to confirm correct functionality for `original_log_method`
    """
    class MyTestClass:
        def log(self):
            pass

    id_log_method = id(MyTestClass.log)
    # Confirm the original log method is unchanged
    orig_log_method = original_log_method(MyTestClass, 'log')
    assert id(orig_log_method) == id_log_method

    # Overwrite the `MyTestClass.log` method
    MyTestClass.log = lambda: print('Hello world!')

    # Confirm the original log method is unchanged
    orig_log_method = original_log_method(MyTestClass, 'log')
    assert id(orig_log_method) == id_log_method

    # Assert the `MyTestClass.log` method was changed, but the original log
    # method is still the same.
    id_log_method = id(MyTestClass.log)
    assert id(orig_log_method) != id_log_method
