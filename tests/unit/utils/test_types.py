import pytest

from aws_teams_logger.utils.types import get_formatted_message


def test_get_formatted_message_with_no_formatting():

    for arg in None, [], ['sample arg']:
        msg = get_formatted_message('testing', arg)
        assert msg == 'testing'

    for arg in None, []:
        msg = get_formatted_message('testing %s', arg)
        assert msg == 'testing %s'


def test_get_formatted_message_with_formatting():
    msg = get_formatted_message('testing %s', ('value', ))
    assert msg == 'testing value'

    msg = get_formatted_message('number %d', (3, ))
    assert msg == 'number 3'

    msg = get_formatted_message('values - %s %d %s', ('hello', 7, 'world'))
    assert msg == 'values - hello 7 world'


def test_get_formatting_raises_errors():
    with pytest.raises(TypeError) as e:
        _ = get_formatted_message('values - %s', ('too', 'many', 'args'))
    assert 'not all arguments converted' in e.exconly()

    with pytest.raises(TypeError) as e:
        _ = get_formatted_message('values - %s %s %s %s', ('too', 'few', 'args'))
    assert 'not enough arguments' in e.exconly()


def test_get_formatting_with_format_mapping():
    msg = get_formatted_message('message: %(key)s', ({'key': 'my-value'},))
    assert msg == 'message: my-value'
