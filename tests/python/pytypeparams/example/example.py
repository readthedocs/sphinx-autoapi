#!/usr/bin/env python3
""" """
from __future__ import annotations
from typing import Callable

def generic_function[T](val: T) -> list[T]:
    pass

def generic_with_bound[T:str](val: T) -> list[T]:
    pass

def multiple_var_function[T, X](val:T) -> X:
    pass

def variadic_generic[*T](val: tuple[*T]) -> list[*T]:
    pass

def paramspec_function[**I](val: Callable[I, int]) -> Callable[I, int]:
    pass

class SimpleGenericClass[T]:
    pass

class GenericWithBases[T](Protocol):
    pass

class ClassWithGenericMethod:

    def simple_generic_method[T](self, val: T) -> T:
        return val


class ClassWithGenericAttr[T]:

    values: list[T]


class ClassWithGenericProperty:

    @property
    def simple[T](self) -> list[T]:
        pass
