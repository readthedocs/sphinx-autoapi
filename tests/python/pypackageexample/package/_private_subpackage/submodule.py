"""Example module

This is a description
"""

DATA = 42


def function(foo, bar):
    """A module level function"""


def _private_function():
    """A function that shouldn't get rendered."""


def not_in_all_function():
    """A function that doesn't exist in __all__ when imported."""


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
