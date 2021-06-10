from typing import Sequence, Any


def divide_chunks(seq: Sequence[Any], n: int):
    """
    Yield successive n-sized chunks from l.
    """
    # looping till length l
    for i in range(0, len(seq), n):
        yield seq[i:i + n]
