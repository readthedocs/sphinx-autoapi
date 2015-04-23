Sphinx AutoAPI
==============

A tool that generates a full API ref (Javadoc style) for your project.
It requires no RST and is fully automated,
while being integrated into Sphinx.

Contents
--------

.. toctree::
   :glob:
   :maxdepth: 2

   config
   templates
   design
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
	autoapi_dir = 'path/to/my/project/files'

Then in your ``index.rst``, add autoapi to your TOC tree:

.. code:: rst

	.. toctree::

	   autoapi/index

See all available configuration options in :doc:`config`.

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
