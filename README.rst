Sphinx AutoAPI
==============

.. image:: https://readthedocs.org/projects/sphinx-autoapi/badge/?version=latest
   :target: https://sphinx-autoapi.readthedocs.org
   :alt: Documentation Status

.. image:: https://travis-ci.org/rtfd/sphinx-autoapi.svg?branch=master
   :target: https://travis-ci.org/rtfd/sphinx-autoapi

.. warning:: This is a pre-release version. Some or all features might not work yet.

Sphinx AutoAPI aims to provide "autodoc" or "javadoc" style documentation for Sphinx.
The aim is to support all programming languages,
be easy to use,
and not require much configuration.

AutoAPI is a parse-only solution for both static and dynamic languages.
This is in contrast to the traditional `Sphinx autodoc <http://sphinx-doc.org/ext/autodoc.html>`_,
which is Python-only and uses code imports.

Full documentation can be found on `Read the Docs <http://sphinx-autoapi.readthedocs.org>`_.

Contents
--------

.. toctree::
   :caption: Main
   :glob:
   :maxdepth: 2

   config
   templates
   design

.. toctree::
   :caption: API
   :glob:
   :maxdepth: 2

   autoapi/index

Basic Workflow
--------------

Sphinx AutoAPI has the following structure:

* Configure directory to look for source files
* Generate JSON from those source files, using language-specific tooling
* Map the JSON into standard AutoAPI Python objects
* Generate RST through Jinja2 templates from those Python objects

This basic framework should be easy to implement in your language of choice.
All you need to do is be able to generate a JSON structure that includes your API and docs for those classes, functions, etc.

Install
-------


First you need to install autoapi:

.. code:: bash
	
	pip install sphinx-autoapi

Then add it to your Sphinx project's ``conf.py``:

.. code:: python

	extensions = ['autoapi.extension']

        # Document Python Code
	autoapi_type = 'python'
	autoapi_dir = 'path/to/python/files'

        # Or, Document Go Code
	autoapi_type = 'go'
	autoapi_dir = 'path/to/go/files'

Then in your ``index.rst``, add autoapi to your TOC tree:

.. code:: rst

	.. toctree::

	   autoapi/index

This is needed because we will be outputting rst files into the ``autoapi`` directory.
This adds it into the global TOCTree for your project,
so that it appears in the menus.

We hope to be able to dynamically add items into the TOCTree, and remove this step.
However, it is currently required.

See all available configuration options in :doc:`config`.

Customize
---------

All of the pages that AutoAPI generates are templated with Jinja2 templates.
You can fully customize how pages are displayed on a per-object basis.
Read more about it in :doc:`templates`.

Design
------

Read more about the deisgn in our :doc:`design`.

Currently Implemented
---------------------

* Python
* .Net
* Go
* Javascript

Adding a new language
---------------------

Adding a new language should only take a couple of hours,
assuming your language has a tool to generate JSON from API documentation.

The steps to follow:

* Add a new Mapper file in `mappers/`. It's probably easiest to copy an existing one, like the Javascript or Python mappers.
* Implement the :py:func:`create_class` and :py:func:`read_file` methods on the :py:class:`SphinxMapperBase`.
* Implement all appropriate object types on the :py:class:`PythonMapperBase`
* Add a test in the `tests/test_integration.py`, along with an example project for the testing.
* Include it in the class mapping in `mappers/base.py` and `extension.py`

