# -*- coding: utf-8 -*-
"""Example module

This is a description
"""
from typing import ClassVar, Dict, Iterable, List, Union

max_rating: int = 10

is_valid: bool
if max_rating > 100:
    is_valid = False
else:
    is_valid = True

ratings: List[int] = [0, 1, 2, 3, 4, 5]

rating_names: Dict[int, str] = {0: "zero", 1: "one"}


def f(start: int, end: int) -> Iterable[int]:
    i = start
    while i < end:
        yield i
        i += 1


mixed_list: List[Union[str, int]] = [1, "two", 3]


def f2(not_yet_a: "A") -> int:
    ...


class A:
    is_an_a: ClassVar[bool] = True
    not_assigned_to: ClassVar[str]

    def __init__(self):
        self.instance_var: bool = True
        """This is an instance_var."""


global_a: A = A()
