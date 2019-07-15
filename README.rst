Sphinx AutoAPI
==============

.. image:: https://readthedocs.org/projects/sphinx-autoapi/badge/?version=latest
    :target: https://sphinx-autoapi.readthedocs.org
    :alt: Documentation

.. image:: https://travis-ci.org/readthedocs/sphinx-autoapi.svg?branch=master
    :target: https://travis-ci.org/readthedocs/sphinx-autoapi
    :alt: Travis Build Status

.. image:: https://ci.appveyor.com/api/projects/status/5nd33gp2eq7411t1?svg=true
    :target: https://ci.appveyor.com/project/ericholscher/sphinx-autoapi
    :alt: Appveyor Build Status

.. image:: https://img.shields.io/pypi/v/sphinx-autoapi.svg
    :target: https://pypi.org/project/sphinx-autoapi/
    :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/sphinx-autoapi.svg
    :target: https://pypi.org/project/sphinx-autoapi/
    :alt: Supported Python Versions

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/python/black
    :alt: Formatted with Black

Sphinx AutoAPI provides "autodoc" style documentation for multiple programming languages
without needing to load, run, or import the project being documented.

In contrast to the traditional `Sphinx autodoc <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_,
which is Python-only and uses code imports,
AutoAPI finds and generates documentation by parsing source code.

Language Support
----------------

==========  ======  ==========================================================
Language    Status  Parser
==========  ======  ==========================================================
Python      Stable  Custom using `astroid <https://github.com/PyCQA/astroid>`_
Go          Alpha   `godocjson <https://github.com/readthedocs/godocjson>`_
Javascript  Alpha   `jsdoc <http://usejsdoc.org/>`_
.NET        Alpha   `docfx <https://dotnet.github.io/docfx/>`_
==========  ======  ==========================================================

Getting Started
---------------

The following steps will walk through how to add AutoAPI to an existing Sphinx project.
For instructions on how to set up a Sphinx project,
see Sphinx's documentation on
`Getting Started <https://www.sphinx-doc.org/en/master/usage/quickstart.html>`_.

Installation
~~~~~~~~~~~~

AutoAPI can be installed through pip:

.. code-block:: bash

    pip install sphinx-autoapi

Next, add and configure AutoAPI in your Sphinx project's `conf.py`.
Other languages may require
`further configuration <https://sphinx-autoapi.readthedocs.io/en/latest/tutorials.html#setting-up-automatic-api-documentation-generation>`_:

.. code-block:: python

    extensions.append('autoapi.extension')

    autoapi_type = 'python'
    autoapi_dirs = ['path/to/source/files', 'src']

Where `autoapi_type` can be one of any of the supported languages:

==========  ================
Language    ``autoapi_type``
==========  ================
Python      ``'python'``
Go          ``'go'``
Javascript  ``'javascript'``
.NET        ``'dotnet'``
==========  ================

When the documentation is built,
AutoAPI will now generate API documentation into an `autoapi/` directory and add an entry to the documentation in your top level table of contents!

To configure AutoAPI behaviour further,
see the `Configuration documentation <https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html>`_.


Contributing
------------

Running the tests
~~~~~~~~~~~~~~~~~

Tests are executed through `tox <https://tox.readthedocs.io/en/latest/>`_.

.. code-block:: bash

    tox

Code Style
~~~~~~~~~~

Code is formatted using `black <https://github.com/python/black>`_.

You can check your formatting using black's check mode:

.. code-block:: bash

    tox -e formatting

You can also get black to format your changes for you:

.. code-block:: bash

    black autoapi/ tests/

You can even get black to format changes automatically when you commit using `pre-commit <https://pre-commit.com/>`_:


.. code-block:: bash

    pip install pre-commit
    pre-commit install

Versioning
----------

We use `SemVer <http://semver.org/>`_ for versioning. For the versions available, see the `tags on this repository <https://github.com/readthedocs/sphinx-autoapi/tags>`_.

License
-------

This project is licensed under the MIT License.
See the `LICENSE.rst <LICENSE.rst>`_ file for details.
