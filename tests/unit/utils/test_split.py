"""
Tests for the module `split`
"""
from typing import List

import pytest

from aws_teams_logger.utils.split import divide_chunks


@pytest.mark.parametrize(
    'input,chunk_size,expected',
    [
        [
            [1, 0, 1],
            1,
            [[1], [0], [1]]
        ],
        [
            ['Hello', 'there', 'world!'],
            2,
            [['Hello', 'there'], ['world!']]
        ],
        [
            [12.75, 127, 15],
            3,
            [[12.75, 127, 15]]
        ],
        [
            [1, 2, 3],
            5,
            [[1, 2, 3]]
        ],
    ]
)
def test_divide_chunks(input: List, chunk_size: int, expected: List[List]):
    actual = list(divide_chunks(input, chunk_size))
    assert actual == expected
