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

.. confval:: autoapi_ignore

	Default: ``[]``

	A list of patterns to ignore when finding files

.. confval:: autoapi_keep_files

	Default: ``False``

	Keep the AutoAPI generated files on the filesystem after the run.
	Useful for debugging.

