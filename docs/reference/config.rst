Configuration Options
=====================

.. confval:: autoapi_dirs

   **Required**

   Paths (relative or absolute) to the source code that you wish to generate your API documentation from.
   The paths are searched recursively for files matching :confval:`autoapi_file_patterns`.
   Relative paths should be relative to the source directory of your documentation.

   For Python, if a package directory is specified,
   the package directory itself will be included in the relative path of the children.
   If an ordinary directory is specified,
   that directory will not be included in the relative path.

.. confval:: autoapi_type

   Default: ``python``

   Set the type of files you are documenting.
   This depends on the programming language that you are using:

   ==========  ================
   Language    ``autoapi_type``
   ==========  ================
   Python      ``'python'``
   Go          ``'go'``
   Javascript  ``'javascript'``
   .NET        ``'dotnet'``
   ==========  ================

.. confval:: autoapi_template_dir

   Default: ``''``

   A directory that has user-defined templates to override our default templates.
   The path can either be absolute,
   or relative to the source directory of your documentation files.
   An path relative to where `sphinx-build` is run
   is allowed for backwards compatibility only
   and will be removed in a future version.

   You can view the default templates in the
   `autoapi/templates <https://github.com/readthedocs/sphinx-autoapi/tree/master/autoapi/templates>`_
   directory of the package.

.. confval:: autoapi_file_patterns

   Default: Varies by Language

   A list containing the file patterns to look for when generating documentation.
   Patterns should be listed in order of preference.
   For example,
   if ``autoapi_file_patterns`` is set to the default value
   and a `.py` file and a `.pyi` file are found,
   then the `.py` will be read.

   The defaults by language are:

   ==========  ============================================
   Language    ``autoapi_file_patterns``
   ==========  ============================================
   Python      ``['*.py', '*.pyi']``
   Go          ``['*.go']``
   Javascript  ``['*.js']``
   .NET        ``['project.json', '*.csproj', '*.vbproj']``
   ==========  ============================================

.. confval:: autoapi_generate_api_docs

   Default: ``True``

   Whether to generate API documentation.
   If this is ``False``, documentation should be generated though the
   :doc:`directives`.


Customisation Options
---------------------

.. confval:: autoapi_options

   Default: [
   ``'members'``,
   ``'undoc-members'``,
   ``'private-members'``,
   ``'show-inheritance'``,
   ``'show-module-summary'``,
   ``'special-members'``,
   ``'imported-members'``,
   ]

   Options for display of the generated documentation.

   * ``members``: Display children of an object
   * ``inherited-members``: Display children of an object
     that have been inherited from a base class.
   * ``undoc-members``: Display objects that have no docstring
   * ``private-members``: Display private objects (eg. ``_foo`` in Python)
   * ``special-members``: Display special objects (eg. ``__foo__`` in Python)
   * ``show-inheritance``: Display a list of base classes below the class signature.
   * ``show-inheritance-diagram``: Display an inheritance diagram in
     generated class documentation.
     It makes use of the :mod:`sphinx.ext.inheritance_diagram` extension,
     and requires `Graphviz <https://graphviz.org/>`_ to be installed.
   * ``show-module-summary``: Whether to include autosummary directives
     in generated module documentation.
   * ``imported-members``: Display objects imported from the same
     top level package or module.
     The default module template does not include imported objects,
     even with this option enabled.
     The default package template does.


.. confval:: autoapi_ignore

   Default: Varies By Language

   A list of patterns to ignore when finding files.
   The defaults by language are:

   ==========  ============================================
   Language    ``autoapi_file_patterns``
   ==========  ============================================
   Python      ``['*migrations*']``
   Go          ``[]``
   Javascript  ``[]``
   .NET        ``['*toc.yml', '*index.yml']``
   ==========  ============================================

.. confval:: autoapi_root

   Default: ``autoapi``

   Path to output the generated AutoAPI files into,
   including the generated index page.
   This path must be relative to the source directory of your documentation files.
   This can be used to place the generated documentation
   anywhere in your documentation hierarchy.

.. confval:: autoapi_add_toctree_entry

   Default: ``True``

   Whether to insert the generated documentation into the TOC tree.
   If this is ``False``, the default AutoAPI index page is not generated
   and you will need to include the generated documentation
   in a TOC tree entry yourself.

.. confval:: autoapi_add_objects_to_toctree

   Default: ``True``

   Whether to insert a TOC tree entry for each object (class, function, etc.).

.. confval:: autoapi_python_class_content

   Default: ``class``

   Which docstring to insert into the content of a class.

   * ``class``: Use only the class docstring.
   * ``both``: Use the concatenation of the class docstring and the
     ``__init__`` docstring.
   * ``init``: Use only the ``__init__`` docstring.

   If the class does not have an ``__init__`` or the ``__init__``
   docstring is empty and the class defines a ``__new__`` with a docstring,
   the ``__new__`` docstring is used instead of the ``__init__`` docstring.

.. confval:: autoapi_member_order

   Default: ``bysource``

   The order to document members. This option can have the following values:

   * ``alphabetical``: Order members by their name, case sensitively.

   * ``bysource``: Order members by the order that they were defined in the source code.

   * ``groupwise``: Order members by their type then alphabetically,
     ordering the types as follows:

     * Submodules and subpackages

     * Attributes

     * Exceptions

     * Classes

     * Functions

     * Methods


.. confval:: autoapi_python_use_implicit_namespaces

   Default: ``False``

   This changes the package detection behaviour to be compatible with :pep:`420`,
   but directories in :confval:`autoapi_dirs`
   are no longer searched recursively for packages.
   Instead, when this is ``True``,
   :confval:`autoapi_dirs` should point directly to
   the directories of implicit namespaces
   and the directories of packages.

   If searching is still required,
   this should be done manually in the ``conf.py``.


.. confval:: autoapi_prepare_jinja_env

   Default: ``None``

   A callback that is called shortly after the Jinja environment is created.
   It passed the Jinja environment for editing before template rendering begins.

   The callback should have the following signature:

   .. py:function:: prepare_jinja_env(jinja_env: jinja2.Environment) -> None
      :noindex:


Events
~~~~~~

The following events allow you to control the behaviour of AutoAPI.

.. event:: autoapi-skip-member (app, what, name, obj, skip, options)

   (Python only)
   Emitted when a template has to decide whether a member should be included
   in the documentation.
   Usually the member is skipped if a handler returns ``True``,
   and included otherwise.
   Handlers should return ``None`` to fall back to the default skipping
   behaviour of AutoAPI or another attached handler.

   .. code-block:: python
      :caption: Example conf.py

      def skip_util_classes(app, what, name, obj, skip, options):
          if what == "class" and "util" in name:
             skip = True
          return skip

      def setup(sphinx):
         sphinx.connect("autoapi-skip-member", skip_util_classes)

   :param app: The Sphinx application object.
   :param what: The type of the object which the docstring belongs to.
      This can be one of:
      ``"attribute"``, ``"class"``, ``"data"``, ``"exception"``,
      ``"function"``, ``"method"``, ``"module"``, ``"package"``.
   :type what: str
   :param name: The fully qualified name of the object.
   :type name: str
   :param obj: The object itself.
   :type obj: PythonPythonMapper
   :param skip: Whether AutoAPI will skip this member if the handler
      does not override the decision.
   :type skip: bool
   :param options: The options given to the directive.


Advanced Options
-----------------

.. confval:: autoapi_keep_files

   Default: ``False``

   Keep the AutoAPI generated files on the filesystem after the run.
   Useful for debugging or transitioning to manual documentation.

   Keeping files will also allow AutoAPI to use incremental builds.
   Providing none of the source files have changed,
   AutoAPI will skip parsing the source code and regenerating the API documentation.


Suppressing Warnings
---------------------

.. confval:: suppress_warnings

   This is a sphinx builtin option that enables the granular filtering of AutoAPI
   generated warnings.

   Items in the ``suppress_warnings`` list are of the format ``"type.subtype"`` where
   ``".subtype"`` can be left out to cover all subtypes. To suppress all AutoAPI
   warnings add the type ``"autoapi"`` to the list:

   .. code-block:: python

      suppress_warnings = ["autoapi"]

   If narrower suppression is wanted, the available subtypes for AutoAPI are:

     * python_import_resolution
       Used if resolving references to objects in an imported module failed. Potential reasons
       include cyclical imports and missing (parent) modules.
     * not_readable
       Emitted if processing (opening, parsing, ...) an input file failed.
     * toc_reference
       Used if a reference to an entry in a table of content cannot be resolved.

   So if all AutoAPI warnings concerning unreadable sources and failing Python imports should be
   filtered, but all other warnings should not, the option would be

   .. code-block:: python

      suppress_warnings = ["autoapi.python_import_resolution", "autoapi.not_readable"]
