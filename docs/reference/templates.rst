Templates
=========

A lot of the power from AutoAPI comes from templates.
We are basically building a mapping from code to docs,
and templates let you highly customise the display of said docs.

Structure
---------

Every type of data structure has its own template.
It uses the form :samp:`{language}/{type}.rst` to find the template to render.
The full search path is:

	* :samp:`{language}/{type}.rst`

So for a .NET Class, this would resolve to:

	* :samp:`dotnet/class.rst`

We provide :samp:`base/base.rst` as an incredibly basic output of every object::

	.. {language}:{type}:: {name}


Custom Filters, Tests, and Globals
----------------------------------

The :confval:`autoapi_prepare_jinja_env` configuration option allows you
to pass a callback that can edit the :class:`jinja2.Environment` object
before rendering begins.
This callback, among other things, can be used to add custom filters,
tests, and/or globals to the Jinja environment. For example:

.. code-block:: python

	def autoapi_prepare_jinja_env(jinja_env):
		jinja_env.filters["my_custom_filter"] = lambda value: value.upper()


Context
-------

Every template is given a set context that can be accessed in the templates.
This contains:

* ``autoapi_options``: The value of the :confval:`autoapi_options`
  configuration option.
* ``include_summaries``: The value of the :confval:`autoapi_include_summaries`
  configuration option.
* ``obj``: A Python object derived from :class:`PythonMapperBase`.
* ``sphinx_version``: The contents of :attr:`sphinx.version_info`.

The object in ``obj`` has a number of standard attributes
that you can reliably access per language.

.. warning::

	These classes should not be constructed manually.
	They can be reliably accessed through templates only.

Python
~~~~~~

.. autoapiclass:: autoapi.mappers.python.objects.PythonPythonMapper
	:members:

.. autoapiclass:: autoapi.mappers.python.objects.PythonFunction
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonMethod
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonProperty
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonData
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonAttribute
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.TopLevelPythonPythonMapper
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonModule
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonPackage
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonClass
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi.mappers.python.objects.PythonException
	:members:
	:show-inheritance:

Go
~~~

.. autoapiclass:: autoapi.mappers.go.GoPythonMapper
	:members:

Javascript
~~~~~~~~~~

.. autoapiclass:: autoapi.mappers.javascript.JavaScriptPythonMapper
	:members:

.NET
~~~~

.. autoapiclass:: autoapi.mappers.dotnet.DotNetPythonMapper
	:members:
