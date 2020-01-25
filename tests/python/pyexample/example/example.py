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

    class Meta(object):
        """A nested class just to test things out"""

        @classmethod
        def foo():
            """The foo class method"""
            return True

    def __init__(self, attr):
        """Constructor docstring"""
        self.attr = attr
        self.attr2 = attr
        """This is the docstring of an instance attribute.

        :type: str
        """

    def method_okay(self, foo=None, bar=None):
        """This method should parse okay"""
        return True

    def method_multiline(self, foo=None, bar=None, baz=None):
        """This is on multiple lines, but should parse okay too

        pydocstyle gives us lines of source. Test if this means that multiline
        definitions are covered in the way we're anticipating here
        """
        return True

    def method_tricky(self, foo=None, bar=dict(foo=1, bar=2)):
        """This will likely fail our argument testing

        We parse naively on commas, so the nested dictionary will throw this off
        """
        return True

    def method_sphinx_docs(self, foo, bar=0):
        """This method is documented with sphinx style docstrings.

        :param foo: The first argument.
        :type foo: int

        :param int bar: The second argument.

        :returns: The sum of foo and bar.
        :rtype: int
        """
        return foo + bar

    def method_google_docs(self, foo, bar=0):
        """This method is documented with google style docstrings.

        Args:
            foo (int): The first argument.
            bar (int): The second argument.

        Returns:
            int: The sum of foo and bar.
        """
        return foo + bar

    def method_sphinx_unicode(self):
        """This docstring uses unicodé.

        :returns: A string.
        :rtype: str
        """
        return "sphinx"

    def method_google_unicode(self):
        """This docstring uses unicodé.

        Returns:
            str: A string.
        """
        return "google"


def decorator_okay(func):
    """This decorator should parse okay."""

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class Bar(Foo):
    pass
