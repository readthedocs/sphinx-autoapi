Directives
==========

.. _autodoc-directives:

Autodoc-Style Directives
------------------------

You can opt to write API documentation yourself using autodoc style directives.
These directives work similarly to autodoc,
but docstrings are retrieved through static analysis instead of through imports.

.. seealso::

    When transitioning to autodoc-style documentation,
    you may want to turn the :confval:`autoapi_generate_api_docs`
    option off so that automatic API documentation is no longer generated.

To use these directives you will need to enable the autodoc extension
in your Sphinx project's ``conf.py``:

.. code:: python

    extensions = ['sphinx.ext.autodoc', 'autoapi.extension']


For Python, all directives have an autodoc equivalent
and accept the same options.
The following directives are available:

.. rst:directive:: autoapimodule
                   autoapiclass
                   autoapiexception

    Equivalent to :rst:dir:`automodule`, :rst:dir:`autoclass`,
    and :rst:dir:`autoexception` respectively.
    :confval:`autodoc_inherit_docstrings` does not currently work.

.. rst:directive:: autoapifunction
                   autoapidata
                   autoapimethod
                   autoapiattribute

    Equivalent to :rst:dir:`autofunction`, :rst:dir:`autodata`,
    :rst:dir:`automethod`, and :rst:dir:`autoattribute` respectively.


Inheritance Diagrams
--------------------

.. rst:directive:: autoapi-inheritance-diagram

    This directive uses the :mod:`sphinx.ext.inheritance_diagram` extension
    to create inheritance diagrams for classes.

    For example:

    .. autoapi-inheritance-diagram:: autoapi.mappers.python.objects.PythonModule autoapi.mappers.python.objects.PythonPackage
        :parts: 1

    :mod:`sphinx.ext.inheritance_diagram` makes use of the
    :mod:`sphinx.ext.graphviz` extension,
    and therefore it requires `Graphviz <https://graphviz.org/>`_ to be installed.

    The directive can be configured using the same options as
    :mod:`sphinx.ext.inheritance_diagram`.
