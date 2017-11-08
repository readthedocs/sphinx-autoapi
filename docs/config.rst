AutoAPI Configuration
=====================

Configuration Options
---------------------

.. confval:: autoapi_dirs

	**Required**

        Paths (relative or absolute) to the source code that you wish to generate your API documentation from.

.. confval:: autoapi_type

	Default: ``python``

	Set the type of files you are documenting

.. confval:: autoapi_template_dir

	Default: ``''``

	A directory that has user-defined templates to override our default templates.

        You can see the existing files in the `autoapi/templates`_ directory.

.. confval:: autoapi_file_patterns

	Default: ``Varies by Language``

        A list containing the file patterns to look for when generating documentation. Python for example is ``['*.py']``.

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

	Relative path to output the AutoAPI files into

.. confval:: autoapi_include_summaries

	Default: ``False``

	Whether include autosummary directives in generated module documentation.

Debugging Options
-----------------

.. confval:: autoapi_keep_files

	Default: ``False``

	Keep the AutoAPI generated files on the filesystem after the run.
	Useful for debugging.

.. _autoapi/templates:: https://github.com/rtfd/sphinx-autoapi/tree/master/autoapi/templates
