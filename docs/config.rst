AutoAPI Configuration
---------------------

.. confval:: autoapi_dir

	**Required**

	Where to find the files to generate the AutoAPI from.

.. confval:: autoapi_type

	Default: ``dotnet``

	Set the type of files you are documenting

.. confval:: autoapi_root

	Default: ``autoapi``

	Directory to output the AutoAPI files into

.. confval:: autoapi_template_dir

	Default: ``''``

	A directory that has user-defined templates to override our default templates.

.. confval:: autoapi_ignore

	Default: ``[]``

	A list of patterns to ignore when finding files

.. confval:: autoapi_keep_files

	Default: ``False``

	Keep the AutoAPI generated files on the filesystem after the run.
	Useful for debugging.

.. confval:: autoapi_options

	Default: ``['members', 'undoc-members', 'private-members', 'special-members']``

	Options for display of the documentation.

	:param members: Display children of an object
	:param undoc-members: Display undocumented object
	:param private-members: Display private objects (_foo in Python)
	:param special-members: Display special objects (__foo__ in Python)

