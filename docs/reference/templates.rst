Templates
=========

A lot of the power from AutoAPI comes from templates.
We are basically building a mapping from code to docs,
and templates let you highly customise the display of said docs.

Structure
---------

Every type of data structure has its own template.
It uses the form :samp:`python/{type}.rst` to find the template to render.
The full search path is:

	* :samp:`python/{type}.rst`

So for a Python Class, this would resolve to:

	* :samp:`python/class.rst`

We provide :samp:`base/base.rst` as an incredibly basic output of every object::

	.. py:{type}:: {name}


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
* ``obj``: A Python object derived from :class:`PythonPythonMapper`.
* ``own_page_types``: A set of strings that contains the object types that
  render on their own page.
* ``sphinx_version``: The contents of :attr:`sphinx.version_info`.

The object in ``obj`` has a number of standard attributes
that you can reliably access.

.. warning::

	These classes should not be constructed manually.
	They can be reliably accessed through templates
	and :event:`autoapi-skip-member` only.

.. autoapiclass:: autoapi._objects.TopLevelPythonPythonMapper
	:members:

.. autoapiclass:: autoapi._objects.PythonFunction
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonMethod
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonProperty
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonData
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonAttribute
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonModule
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonPackage
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonClass
	:members:
	:show-inheritance:

.. autoapiclass:: autoapi._objects.PythonException
	:members:
	:show-inheritance:
