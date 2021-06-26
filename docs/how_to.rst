How-to Guides
=============

.. _customise-templates:

How to Customise Layout Through Templates
-----------------------------------------

You can customise the look of the documentation that AutoAPI generates
by changing the Jinja2 templates that it uses.
The default templates live in the ``autoapi/templates`` directory of the AutoAPI package.
Simply copy whichever templates you want to customise to a local directory
and edit them.
To get AutoAPI to use these templates,
point the :confval:`autoapi_template_dir` configuration option to your directory.
It can be absolute, or relative to the root of the documentation source directory
(ie the directory passed to ``sphinx-build``).

.. code-block:: python

    autoapi_template_dir = '_autoapi_templates'

Your template directory must to follow the same layout as the default templates.
For example, to override the Python class and module templates:

.. code-block:: none

    _autoapi_templates
    └── python
        ├── class.rst
        └── module.rst


How to Customise the Index Page
-------------------------------

The index page that AutoAPI creates is generated using a template.
So customising the index page follows the same steps as customising a template.
Simply edit the ``autoapi/templates/index.rst`` template
with the same steps as :ref:`customising a template <customise-templates>`.


How to Remove the Index Page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To remove the index page altogether,
turn off the :confval:`autoapi_add_toctree_entry` configuration option::

    autoapi_add_toctree_entry = False

You will then need to include the generated documentation in the toctree yourself.
For example if you were generating documentation for a package called "example",
you would add the following toctree entry::

    .. toctree::

        autoapi/example/index

Note that ``autoapi/`` is the default location of documentation,
as configured by :confval:`autoapi_root`.
If you change :confval:`autoapi_root`,
then the entry that you need to add would change also.


How to Configure Where Documentation Appears in the TOC Tree
------------------------------------------------------------

The :confval:`autoapi_root` configuration option defines where generated documentation is output.
To change where documentation is output,
simply change this option to another directory relative to the documentation source directory:

.. code-block:: python

    autoapi_root = 'technical/api'


How to Transition to Autodoc-Style Documentation
----------------------------------------------------

Once you have written some documentation with the :ref:`autodoc-directives`,
turning the automatic documentation generation off is as easy as
disabling the :confval:`autoapi_generate_api_docs` configuration option::

    autoapi_generate_api_docs = False


How to Transition to Manual Documentation
-----------------------------------------

To start writing API documentation yourself,
you can get AutoAPI to keep its generated files around as a base to start from
using the :confval:`autoapi_keep_files` option::

    autoapi_keep_files = True

Once you have built your documentation with this option turned on,
you can disable AutoAPI altogether from your project.


How to Include Type Annotations as Types in Rendered Docstrings
---------------------------------------------------------------

.. warning::

    This feature is experimental and may change or be removed in future versions.

Since v3.0, :mod:`sphinx` has included an :mod:`sphinx.ext.autodoc.typehints`
extension that is capable of rendering type annotations as
parameter types and return types.

For example the following function:

.. code-block::

    def _func(a: int, b: Optional[str]) -> bool
        """My function.

        :param a: The first arg.
        :param b: The second arg.

        :returns: Something.
        """

would be rendered as:

.. py:function:: _func(a, b)
    :noindex:

    :param int a: The first arg.
    :param b: The second arg.
    :type b: Optional[str]

    :returns: Something.
    :rtype: bool

AutoAPI is capable of the same thing.
To enable this behaviour, load the :mod:`sphinx.ext.autodoc.typehints`
(or :mod:`sphinx.ext.autodoc`) extension in Sphinx's ``conf.py`` file
and set :confval:`autodoc_typehints` to ``description`` as normal::

    extensions = ['sphinx.ext.autodoc', 'autoapi.extension']
    autodoc_typehints = 'description'

.. note::

    Unless :confval:`autodoc_typehints` is set to ``none``,
    the type annotations of overloads will always be output in the signature
    and never merged into the description
    because it is impossible to represent all overloads as a list of parameters.
