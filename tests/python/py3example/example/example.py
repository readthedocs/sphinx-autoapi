# -*- coding: utf-8 -*-
"""Example module

This is a description
"""
import asyncio
import typing
from typing import ClassVar, Dict, Iterable, List, Union, overload

max_rating: int = 10

is_valid: bool
if max_rating > 100:
    is_valid = False
else:
    is_valid = True

ratings: List[int] = [0, 1, 2, 3, 4, 5]

rating_names: Dict[int, str] = {0: "zero", 1: "one"}


def f(start: int, end: int) -> Iterable[int]:
    "This is f"
    i = start
    while i < end:
        yield i
        i += 1


mixed_list: List[Union[str, int]] = [1, "two", 3]
"This is mixed"


def f2(not_yet_a: "A") -> int:
    ...


@overload
def overloaded_func(a: float) -> float:
    ...


@typing.overload
def overloaded_func(a: str) -> str:
    ...


def overloaded_func(a: Union[float, str]) -> Union[float, str]:
    """Overloaded function"""
    return a * 2


@overload
def undoc_overloaded_func(a: str) -> str:
    ...


def undoc_overloaded_func(a: str) -> str:
    return a * 2


class A:
    """class A"""

    is_an_a: ClassVar[bool] = True
    not_assigned_to: ClassVar[str]

    def __init__(self):
        self.instance_var: bool = True
        """This is an instance_var."""

    async def async_method(self, wait: bool) -> int:
        if wait:
            await asyncio.sleep(1)
        return 5

    @property
    def my_prop(self) -> str:
        """My property."""
        return "prop"

    def my_method(self) -> str:
        """My method."""
        return "method"

    @overload
    def overloaded_method(self, a: float) -> float:
        ...

    @typing.overload
    def overloaded_method(self, a: str) -> str:
        ...

    def overloaded_method(self, a: Union[float, str]) -> Union[float, str]:
        """Overloaded method"""
        return a * 2

    @overload
    def undoc_overloaded_method(self, a: float) -> float:
        ...

    def undoc_overloaded_method(self, a: float) -> float:
        return a * 2

    @typing.overload
    @classmethod
    def overloaded_class_method(cls, a: float) -> float:
        ...

    @overload
    @classmethod
    def overloaded_class_method(cls, a: str) -> str:
        ...

    @classmethod
    def overloaded_class_method(cls, a: Union[float, str]) -> Union[float, str]:
        """Overloaded class method"""
        return a * 2


async def async_function(self, wait: bool) -> int:
    if wait:
        await asyncio.sleep(1)

    return 5


global_a: A = A()
