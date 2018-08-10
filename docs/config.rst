AutoAPI Configuration
=====================

Configuration Options
---------------------

.. confval:: autoapi_dirs

	**Required**

        Paths (relative or absolute) to the source code that you wish to generate your API documentation from.

		If a package directory is specified, the package directory itself will be included in the relative path of the
		children. If an ordinary directory is specified, that directory will not be included in the relative path.

.. confval:: autoapi_type

	Default: ``python``

	Set the type of files you are documenting

.. confval:: autoapi_template_dir

	Default: ``''``

	A directory that has user-defined templates to override our default templates.

        You can see the existing files in the `autoapi_templates`_ directory.

.. confval:: autoapi_file_patterns

	Default: ``Varies by Language``

        A list containing the file patterns to look for when generating documentation. Python for example is ``['*.py']``.

... confval:: autoapi_generate_api_docs

	Default: ``True``

	Whether to generate API documentation.
	If this is ``False``, documentation should be generated though the
	:doc:`directives`.


Customization Options
---------------------

.. confval:: autoapi_options

	Default: ``['members', 'undoc-members', 'private-members', 'special-members']``

	Options for display of the documentation.

	:param members: Display children of an object
	:param undoc-members: Display undocumented object
	:param private-members: Display private objects (_foo in Python)
	:param special-members: Display special objects (__foo__ in Python)


.. confval:: autoapi_ignore

	Default: ``[]``

	A list of patterns to ignore when finding files

.. confval:: autoapi_root

	Default: ``autoapi``

	Relative path to output the AutoAPI files into.
	This can also be used to place the generated documentation
	anywhere in your documentation hierarchy.

.. confval:: autoapi_add_toctree_entry

	Default: ``True``

	Whether to insert the generated documentation into the toctree.
	If this is False, the default AutoAPI index page is not generated.
	You will also need to include the generated documentation
	in a toctree entry yourself.

	This can be used with :confval:`autoapi_root` to place
	the generated documentation somewhere other than the root.

.. confval:: autoapi_include_summaries

	Default: ``False``

	Whether include autosummary directives in generated module documentation.

.. confval:: autoapi_python_class_content

	Default: ``class``

	Which docstring to insert into the content of the class.

	:param class: Use only the class docstring.
	:param both: Use the concatentation of the class docstring and the
		``__init__``/``__new__`` docstring.
	:param init: Use only the ``__init__``/``__new__`` docstring.

	If the class does not have an ``__init__`` or the ``__init__``
	docstring is empty and the class defines a ``__new__`` with a docstring,
	the ``__new__`` docstring is used instead of the ``__init__`` docstring.

Debugging Options
-----------------

.. confval:: autoapi_keep_files

	Default: ``False``

	Keep the AutoAPI generated files on the filesystem after the run.
	Useful for debugging.

.. _autoapi_templates: https://github.com/rtfd/sphinx-autoapi/tree/master/autoapi/templates
