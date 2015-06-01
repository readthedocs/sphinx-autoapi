Sphinx AutoAPI
==============

.. image:: https://readthedocs.org/projects/sphinx-autoapi/badge/?version=latest
   :target: https://readthedocs.org/projects/sphinx-autoapi/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/rtfd/sphinx-autoapi.svg?branch=master
   :target: https://travis-ci.org/rtfd/sphinx-autoapi


A tool that generates a full API ref (Javadoc style) for your project.

It aims to be easy to use,
and not require much configuration.

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

Install
-------

First you need to install autoapi:

.. code:: bash
	
	pip install sphinx-autoapi

Then add it to your Sphinx project's ``conf.py``:

.. code:: python

	extensions = ['autoapi.extension']

	autoapi_type = 'python'
	autoapi_dir = 'path/to/python/files'

Then in your ``index.rst``, add autoapi to your TOC tree:

.. code:: rst

	.. toctree::

	   autoapi/index

This is needed because we will be outputting rst files into the ``autoapi`` directory.
This adds it into the global TOCTree for your project,
so that it appears in the menus.

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

Future
------
Our goal is to support the following soon:

* Javascript
* PHP
* Python
* Go
