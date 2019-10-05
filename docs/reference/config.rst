Configuration Options
=====================

.. confval:: autoapi_dirs

	**Required**

	Paths (relative or absolute) to the source code that you wish to generate your API documentation from.

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

	You can view the default templates in the
	`autoapi/templates <https://github.com/rtfd/sphinx-autoapi/tree/master/autoapi/templates>`_
	directory of the package.

.. confval:: autoapi_file_patterns

	Default: Varies by Language

	A list containing the file patterns to look for when generating documentation.
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

	Default: ``['members', 'undoc-members', 'private-members', 'special-members']``

	Options for display of the documentation.

	* ``members``: Display children of an object
	* ``undoc-members``: Display objects that have no docstring
	* ``private-members``: Display private objects (eg. ``_foo`` in Python)
	* ``special-members``: Display special objects (eg. ``__foo__`` in Python)

.. confval:: autoapi_ignore

	Default: Varies By Language

	A list of patterns to ignore when finding files
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
	This path should be relative to the root of the documentation directory
	(ie the directory with the ``conf.py`` file).
	This can be used to place the generated documentation
	anywhere in your documentation hierarchy.

.. confval:: autoapi_add_toctree_entry

	Default: ``True``

	Whether to insert the generated documentation into the TOC tree.
	If this is ``False``, the default AutoAPI index page is not generated
	and you will need to include the generated documentation
	in a TOC tree entry yourself.

.. confval:: autoapi_include_summaries

	Default: ``False``

	Whether include autosummary directives in generated module documentation.
	This is a shortcut for needing to edit the templates yourself.

.. confval:: autoapi_python_class_content

	Default: ``class``

	Which docstring to insert into the content of a class.

	* ``class``: Use only the class docstring.
	* ``both``: Use the concatentation of the class docstring and the
	  ``__init__`` docstring.
	* ``init``: Use only the ``__init__`` docstring.

	If the class does not have an ``__init__`` or the ``__init__``
	docstring is empty and the class defines a ``__new__`` with a docstring,
	the ``__new__`` docstring is used instead of the ``__init__`` docstring.

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


Debugging Options
-----------------

.. confval:: autoapi_keep_files

	Default: ``False``

	Keep the AutoAPI generated files on the filesystem after the run.
	Useful for debugging or transitioning to manual documentation.
