"""This is a docstring."""

from . import submodule

DATA = 42


def function(foo, bar):
    """A module level function"""


class Class(object):
    """This is a class."""

    class_var = 42
    """Class var docstring"""

    class NestedClass(object):
        """A nested class just to test things out"""

        @classmethod
        def a_classmethod():
            """A class method"""
            return True

    @property
    def my_property(self):
        """A property."""
        return 42

    def method_okay(self, foo=None, bar=None):
        """This method should parse okay"""
        return True


class MyException(Exception):
    """This is an exception."""
