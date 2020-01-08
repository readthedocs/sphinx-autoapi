# -*- coding: utf-8 -*-
"""Example module

This is a description
"""
from typing import ClassVar, Dict, Iterable, List, Union

max_rating = 10  # type: int

ratings = [0, 1, 2, 3, 4, 5]  # type: List[int]

rating_names = {0: "zero", 1: "one"}  # type: Dict[int, str]


def f(
    start,  # type: int
    end,  # type: int
):  # type: (...) -> Iterable[int]
    i = start
    while i < end:
        yield i
        i += 1


mixed_list = [1, "two", 3]  # type: List[Union[str, int]]


def f2(not_yet_a):
    # type: (A) -> int
    pass


class A:
    is_an_a = True  # type: ClassVar[bool]

    def __init__(self):
        self.instance_var = True  # type: bool
        """This is an instance_var."""


global_a = A()  # type: A


def f3(first_arg, **kwargs):
    # type: (first_arg, Any) -> None
    """Annotation incorrectly leaves out `**`."""
