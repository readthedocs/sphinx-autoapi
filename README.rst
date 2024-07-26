Sphinx AutoAPI
==============

.. image:: https://readthedocs.org/projects/sphinx-autoapi/badge/?version=latest
    :target: https://sphinx-autoapi.readthedocs.org
    :alt: Documentation

.. image:: https://github.com/readthedocs/sphinx-autoapi/actions/workflows/main.yml/badge.svg?branch=main
    :target: https://github.com/readthedocs/sphinx-autoapi/actions/workflows/main.yml?query=branch%3Amain
    :alt: Github Build Status

.. image:: https://img.shields.io/pypi/v/sphinx-autoapi.svg
    :target: https://pypi.org/project/sphinx-autoapi/
    :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/sphinx-autoapi.svg
    :target: https://pypi.org/project/sphinx-autoapi/
    :alt: Supported Python Versions

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/python/black
    :alt: Formatted with Black

Sphinx AutoAPI is a Sphinx extension for generating complete API documentation
without needing to load, run, or import the project being documented.

In contrast to the traditional `Sphinx autodoc <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_,
which requires manual authoring and uses code imports,
AutoAPI finds and generates documentation by parsing source code.

For more information, see `the full documentation <https://sphinx-autoapi.readthedocs.org>`_.

Getting Started
---------------

The following steps will walk through how to add AutoAPI to an existing Sphinx project.
For instructions on how to set up a Sphinx project,
see `Sphinx's documentation <https://www.sphinx-doc.org/en/master/usage/quickstart.html>`_.

Installation
~~~~~~~~~~~~

AutoAPI can be installed through pip:

.. code-block:: bash

    pip install sphinx-autoapi

Next, add and configure AutoAPI in your Sphinx project's `conf.py`.

.. code-block:: python

    extensions.append('autoapi.extension')

    autoapi_dirs = ['path/to/source/files', 'src']

When the documentation is built,
AutoAPI will now generate API documentation into an `autoapi/` directory
and add an entry to the documentation in your top level table of contents!

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

    tox -e format

You can also get black to format your changes for you:

.. code-block:: bash

    black autoapi/ tests/

You can even get black to format changes automatically when you commit using `pre-commit <https://pre-commit.com/>`_:


.. code-block:: bash

    pip install pre-commit
    pre-commit install

Release Notes
~~~~~~~~~~~~~

Release notes are managed through `towncrier <https://towncrier.readthedocs.io/en/stable/index.html>`_.
When making a pull request you will need to create a news fragment to document your change:

.. code-block:: bash

    tox -e release_notes -- create --help

Versioning
----------

We use `SemVer <https://semver.org/>`_ for versioning. For the versions available, see the `tags on this repository <https://github.com/readthedocs/sphinx-autoapi/tags>`_.

License
-------

This project is licensed under the MIT License.
See the `LICENSE.rst <LICENSE.rst>`_ file for details.
