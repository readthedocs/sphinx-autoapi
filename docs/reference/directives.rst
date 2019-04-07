.. _autodoc-directives:

Autodoc-Style Directives
========================

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
