"""This is a docstring."""

from . import submodule
from .subpackage.submodule import function as aliased_function
from .subpackage.submodule import not_in_all_function

__all__ = (
    "aliased_function",
    "Class",
    "DATA",
    "function",
    "MyException",
)

DATA = 42


def function(foo, bar):
    """A module level function"""


class Class:
    """This is a class."""

    class_var = 42
    """Class var docstring"""

    class NestedClass:
        """A nested class just to test things out"""

        @classmethod
        def a_classmethod():
            """A class method"""
            return True

    def method_okay(self, foo=None, bar=None):
        """This method should parse okay"""
        return True


class MyException(Exception):
    """This is an exception."""
