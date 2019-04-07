Release Process
===============

This page documents the steps to be taken to release a new version of Sphinx AutoAPI.

Pre-Checks
----------

1. Check that the dependencies of the package are correct.
2. Clean the ``.tox`` directory and run the tests.
3. Commit and push any changes needed to make the tests pass.
4. Check that the tests passed on travis and appveyor.

Preparation
-----------

1. Update the version number in ``setup.py`` and ``docs/conf.py``.
2. Add any missing changelog entries.
3. Put the version number and release date into the changelog.
4. Commit and push the changes.
5. Check that the tests passed on travis and appveyor.

Release
-------

.. code-block:: bash

    git clean -fdx
    python setup.py sdist bdist_wheel
    twine upload dist/*
