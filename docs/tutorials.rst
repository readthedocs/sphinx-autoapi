Tutorials
=========

Setting up Automatic API Documentation Generation
-------------------------------------------------

This tutorial will assume that you already have a basic Sphinx project set up.
If you are not sure how to do this,
you can follow the :doc:`sphinx:usage/quickstart` guide in the Sphinx documentation.

The recommended way of installing AutoAPI is through a `virtualenv <https://virtualenv.pypa.io/>`_.
Once you have a virtualenv set up, you can install AutoAPI with the command:

==========   ======================================
Language     Command
==========   ======================================
Python       ``pip install sphinx-autoapi``
Go           ``pip install sphinx-autoapi[go]``
Javascript   ``pip install sphinx-autoapi``
.NET         ``pip install sphinx-autoapi[dotnet]``
==========   ======================================

Depending on which language you are trying to document,
each language has a different set of steps for finishing the setup of AutoAPI:

.. contents::
    :local:
    :backlinks: none


Python
^^^^^^

To enable the extension,
we need to add it to the list of extensions in Sphinx's ``conf.py`` file::

    extensions = ['autoapi.extension']

For Python, there is only one required configuration option that we need to set.
:confval:`autoapi_dirs` tells AutoAPI which directories contain
the source code to document.
These can either be absolute, or relative to the source directory of
your documentation files.
For example, say we have a package and we have used ``sphinx-quickstart``
to create a Sphinx project in a ``docs/`` folder.
The directory structure might look like this:

.. code-block:: none

    mypackage/
    ├── docs
    │   ├── _build
    │   ├── conf.py
    │   ├── index.rst
    │   ├── make.bat
    │   ├── Makefile
    │   ├── _static
    │   └── _templates
    ├── mypackage
    │   ├── _client.py
    │   ├── __init__.py
    │   └── _server.py
    └── README.md

``sphinx-quickstart`` sets up the ``sphinx-build`` to run from
inside the ``docs/`` directory, and the source code is one level up.
So the value of our :confval:`autoapi_dirs` option would be::

    autoapi_dirs = ['../mypackage']

If you are documenting many packages,
you can point AutoAPI to the directory that contains those packages.
For example if our source code was inside a ``src/`` directory:

.. code-block:: none

    mypackage/
    ├── docs
    │   ├── _build
    │   ├── conf.py
    │   ├── index.rst
    │   ├── make.bat
    │   ├── Makefile
    │   ├── _static
    │   └── _templates
    ├── README.md
    └── src
        └── mypackage
            ├── _client.py
            ├── __init__.py
            └── _server.py

We can configure :confval:`autoapi_dirs` to be::

    autoapi_dirs = ['../src']

Now that everything is configured,
AutoAPI will generate documentation when you run Sphinx!

.. code-block:: bash

    cd docs/
    sphinx-build -b html . _build


Go
^^^

Support for Go requires you to have the go environment installed
(https://golang.org/dl/), as well as our godocjson tool::

    go get github.com/readthedocs/godocjson

and the Go domain extension for Sphinx::

    pip install sphinxcontrib-golangdomain

To enable the AutoAPI extension,
we need to add it to the list of extensions in Sphinx's ``conf.py`` file
with the Go domain extension::

    extensions = [
        'sphinxcontrib.golangdomain',
        'autoapi.extension',
    ]

For Go, there are two required configuration options that we need to set.
:confval:`autoapi_type` tells AutoAPI what type of language we are documenting.
For Go, this is::

    autoapi_type = 'go'

The second configuration option is :confval:`autoapi_dirs`,
which tells AutoAPI which directories contain the source code to document.
These can either be absolute, or relative to the source directory of
your documentation files.
So if your documentation was inside a ``docs/`` directory
and your source code is in an ``example`` directory one level up,
you would configure :confval:`autoapi_dirs` to be::

    autoapi_dirs = ['../example']

Now that everything is configured,
AutoAPI will generate documentation when you run Sphinx!

.. code-block:: bash

    cd docs/
    sphinx-build -b html . _build


Javascript
^^^^^^^^^^

Support for Javascript requires you to have jsdoc (http://usejsdoc.org/) installed::

    npm install jsdoc -g

To enable the AutoAPI extension,
we need to add it to the list of extensions in Sphinx's ``conf.py`` file::

    extensions = ['autoapi.extension']

For Javascript, there are two required configuration options that we need to set.
:confval:`autoapi_type` tells AutoAPI what type of language we are documenting.
For Javascript, this is::

    autoapi_type = 'javascript'

The second configuration option is :confval:`autoapi_dirs`,
which tells AutoAPI which directories contain the source code to document.
These can either be absolute, or relative to the source directory of
your documentation files.
So if your documentation was inside a ``docs/`` directory
and your source code is in an ``example`` directory one level up,
you would configure :confval:`autoapi_dirs` to be::

    autoapi_dirs = ['../example']

Now that everything is configured,
AutoAPI will generate documentation when you run Sphinx!

.. code-block:: bash

    cd docs/
    sphinx-build -b html . _build


.NET
^^^^

Support for .NET requires you to have the docfx (https://dotnet.github.io/docfx/) tool installed,
as well as the .NET domain extension for Sphinx::

    pip install sphinxcontrib-dotnetdomain

Firstly, we need to configure docfx to output to a directory known to AutoAPI.
By default, ``docfx`` will output metadata files into the ``_api`` path.
You can configure which path to output files into by setting the path in your
`docfx configuration file <https://dotnet.github.io/docfx/tutorial/docfx.exe_user_manual.html#3-docfx-json-format>`_
in your project repository.
For example, if your documentation source files are located inside a ``docs/`` directory:

.. code:: json

    {
      "metadata": [{
        "dest": "docs/_api"
      }]
    }

To enable the AutoAPI extension,
we need to add it to the list of extensions in Sphinx's ``conf.py`` file
with the .NET domain extension::

    extensions = [
        'sphinxcontrib.dotnetdomain',
        'autoapi.extension',
    ]

For .NET, there are two required configuration options that we need to set.
:confval:`autoapi_type` tells AutoAPI what type of language we are documenting.
For .NET, this is::

    autoapi_type = 'dotnet'

The second configuration option is :confval:`autoapi_dirs`,
which tells AutoAPI which directories contain the source code to document.
These can either be absolute, or relative to the source directory of
your documentation files.
So if your documentation was inside a ``docs/`` directory
and your source code is in an ``example`` directory one level up,
you would configure :confval:`autoapi_dirs` to be::

    autoapi_dirs = ['../example']

Now that everything is configured,
AutoAPI will generate documentation when you run Sphinx!

.. code-block:: bash

    cd docs/
    sphinx-build -b html . _build
