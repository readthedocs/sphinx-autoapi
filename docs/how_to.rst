How-to Guides
=============

These guides will take you through the steps to perform common actions
or solve common problems in AutoAPI.
They will assume that you already have a Sphinx project with AutoAPI
set up already.
If you don't know how to do this then read the :doc:`tutorials`.


.. _customise-documented-api:

How to Customise What Gets Documented
-------------------------------------

With the default settings,
AutoAPI will document everything that is publicly accessible through the actual package
when loaded in Python.
For example if a function is imported from a submodule into a package
then that function is documented in both the submodule and the package.

.. note::

    The one exception to this rule is that any object imported into a module
    is not documented by default.

However there are multiple options available for controlling what AutoAPI will document.


Set ``__all__``
^^^^^^^^^^^^^^^

AutoAPI treats the definition of `__all__ <https://docs.python.org/tutorial/modules.html#importing-from-a-package>`_
as the specification of what objects are public in a module or package, and which aren't.

In the following example, only ``func_a()`` and ``A`` would be documented.

.. code-block:: python

    # mypackage/__init__.py
    from . import B

    __all__ = ("A", "func_a")

    class A:
        ...

    def func_a():
        ...

    def func_b():
        ...


Configure :confval:`autoapi_options`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :confval:`autoapi_options` configuration value gives some high level control
over what is documented.

For example you could remove ``private-members`` from :confval:`autoapi_options`
and hide your object definitions in private modules.

.. code-block:: python

    # package/__init__.py
    from ._submodule import public_function

    # package/_submodule.py

    def public_function():
        """This public function will be documented only in ``package``."""
        ...

    def private_function()
        """This private function won't be documented."""
        ...

As another example, you could remove ``undoc-members`` from :confval:`autoapi_options`
and only add docstrings for the modules and other entities that you want to be documented.

See :confval:`autoapi_options` for more information on how to use this option.


Connect to the :event:`autoapi-skip-member` event
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :event:`autoapi-skip-member` event is emitted whenever
a template has to decide whether a member should be included in the documentation.

For example, to document only packages
-- in other words, to not document submodules --
you could implement an event handler in your conf.py like the following.

.. code-block:: python

    def skip_submodules(app, what, name, obj, skip, options):
        if what == "module":
            skip = True
        return skip


    def setup(sphinx):
        sphinx.connect("autoapi-skip-member", skip_submodules)


Customise the API Documentation Templates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Finally, you can configure what gets rendered by customising the templates.
This is a rather heavy handed approach,
so it should only be necessary when the other options do not give you
the control the you need.
You can learn how to customise the templates in the next section:
:ref:`customise-templates`.


.. _customise-templates:

How to Customise Layout Through Templates
-----------------------------------------

.. warning::

    Templates control a lot of behaviour,
    so customising templates can mean that you lose out on new functionality
    until you update your customised templates after a new release of AutoAPI.

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


.. _customise-index-page:

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

    Unless :confval:`autodoc_typehints` is set to ``None``,
    the type annotations of overloads will always be output in the signature
    and never merged into the description
    because it is impossible to represent all overloads as a list of parameters.
