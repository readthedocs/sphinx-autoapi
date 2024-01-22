"""This is a docstring."""

from .submodule import function as aliased_function
from .submodule import not_in_all_function

__all__ = (
    "aliased_function",
    "function",
)


def function(foo, bar):
    """A module level function"""
