# -*- coding: utf-8 -*-
"""Example module

This is a description
"""
from typing import Optional


def f_simple(a, b, /, c, d, *, e, f):
    print(a, b, c, d, e, f)


def f_comment(a, b, /, c, d, *, e, f):
    # type: (int, int, Optional[int], Optional[int], float, float) -> None
    print(a, b, c, d, e, f)


def f_annotation(
    a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float
) -> None:
    print(a, b, c, d, e, f)


def f_arg_comment(
    a,  # type: int
    b,  # type: int
    /,
    c,  # type: Optional[int]
    d,  # type: Optional[int]
    *,
    e,  # type: float
    f,  # type: float
):
    # type: (...) -> None
    print(a, b, c, d, e, f)


def f_no_cd(a: int, b: int, /, *, e: float, f: float):
    print(a, b, e, f)
