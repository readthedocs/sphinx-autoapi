import typing

T = typing.TypeVar("T")
R = typing.TypeVar("R")


def transform(callback: typing.Callable[typing.Concatenate[T, ...], R]) -> R: ...
