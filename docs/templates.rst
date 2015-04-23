Templates
---------

A lot of the power from AutoAPI comes from templates.
We are basically building a mapping from Code to Docs,
and templates let you highly customize the display of said docs.

Structure
~~~~~~~~~

Every type of data structure gets it's own template.
It uses the form :samp:`{language}/{type}.rst` to find the template to render.
The full search path is:

	* :samp:`{language}/{type}.rst`
	* :samp:`{language}/unknown.rst`
	* :samp:`base/unknown.rst`

So for a .Net Class, this would resolve to:

	* :samp:`{dotnet}/{class}.rst`
	* :samp:`{dotnet}/unknown.rst`
	* :samp:`base/unknown.rst`

We provide :samp:`base/member.rst` as an incredibly basic output of every object::

	.. {language}:{type}:: {name}

Context
~~~~~~~

Every template will be given a set context. It will contain:

	* `obj`: A Python object derived from :py:class:`autoapi.base.AutoAPIBase`

This object has a number of standard attributes you can reliably access:

	* **id** - A unique identifier
	* **type** - The objects type, lowercase
	* **name** - A user displayable name
	* **item_map** - A dict with keys containing the types this object has as children, and values of those objects.
