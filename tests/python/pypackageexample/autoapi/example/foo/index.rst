:py:mod:`example.foo`
=====================

.. py:module:: example.foo

.. autoapi-nested-parse::

   Example module

   This is a description



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   example.foo.Foo




.. py:class:: Foo


   Bases: :py:obj:`object`

   
   .. py:class:: Meta


      Bases: :py:obj:`object`

      A nested class just to test things out

      
      .. py:method:: foo()
         :classmethod:

         The foo class method



   .. py:attribute:: class_var
      :value: 42

      

   .. py:attribute:: another_class_var
      :value: 42

      Another class var docstring


   
   .. py:method:: method_okay(foo=None, bar=None)

      This method should parse okay


   
   .. py:method:: method_multiline(foo=None, bar=None, baz=None)

      This is on multiple lines, but should parse okay too

      pydocstyle gives us lines of source. Test if this means that multiline
      definitions are covered in the way we're anticipating here


   
   .. py:method:: method_tricky(foo=None, bar=dict(foo=1, bar=2))

      This will likely fail our argument testing

      We parse naively on commas, so the nested dictionary will throw this off


   
   .. py:method:: method_sphinx_docs(foo, bar=0)

      This method is documented with sphinx style docstrings.

      :param foo: The first argument.
      :type foo: int

      :param int bar: The second argument.

      :returns: The sum of foo and bar.
      :rtype: int


   
   .. py:method:: method_google_docs(foo, bar=0)

      This method is documented with google style docstrings.

      Args:
          foo (int): The first argument.
          bar (int): The second argument.

      Returns:
          int: The sum of foo and bar.




