Release Process
===============

This page documents the steps to be taken to release a new version of Sphinx AutoAPI.

Pre-Checks
----------

1. Check that the dependencies of the package are correct.
2. Clean the ``.tox`` directory and run the tests.
3. Commit and push any changes needed to make the tests pass.
4. Check that the tests passed on github.

Preparation
-----------

1. Update the version numbers in ``autoapi/__init__.py``.
2. Run ``tox -e release_notes -- build``
3. Commit and push the changes.
4. Check that the tests passed on github.

Release
-------

Create a new release in github that tags the commit
and uses the built release notes as the description.
The tag created by the release will trigger the github actions to
build and upload the package to PyPI.