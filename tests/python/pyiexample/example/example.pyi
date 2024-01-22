# -*- coding: utf-8 -*-
"""Example module

This is a description
"""

class Foo(object):
    """Can we parse arguments from the class docstring?

    :param attr: Set an attribute.
    :type attr: str
    """

    class_var = 42  #: Class var docstring

    another_class_var = 42
    """Another class var docstring"""

    class_var_without_value = ...
    """A class var without a value."""

    class Meta(object):
        """A nested class just to test things out"""

        @classmethod
        def foo():
            """The foo class method"""
            ...

    def __init__(self, attr):
        """Constructor docstring"""
        ...

    def method_okay(self, foo=None, bar=None):
        """This method should parse okay"""
        ...

    def method_multiline(self, foo=None, bar=None, baz=None):
        """This is on multiple lines, but should parse okay too

        pydocstyle gives us lines of source. Test if this means that multiline
        definitions are covered in the way we're anticipating here
        """
        ...

    def method_without_docstring(self): ...
