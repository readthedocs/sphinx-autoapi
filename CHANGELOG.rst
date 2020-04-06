Changelog
=========

Versions follow `Semantic Versioning <https://semver.org/>`_ (``<major>.<minor>.<patch>``).

v1.3.0 (2020-04-05)
------------

Breaking Changes
^^^^^^^^^^^^^^^^

* Dropped support for Python 3.4 and 3.5.

Features
^^^^^^^^
* `#151 <https://github.com/readthedocs/sphinx-autoapi/issues/151>`: (Python) Added the ``autoapi_python_use_implicit_namespaces`` option to allow
  AutoAPI to search for implicit namespace packages.
* Added support for Sphinx 2.2 and 2.3.
* Added support for Python 3.8.
* `#140 <https://github.com/readthedocs/sphinx-autoapi/issues/140>`: (Python)
  Added the ``autoapi-inheritance-diagram`` directive to create
  inheritance diagrams without importing modules.
  Enable the ``show-inheritance-diagram`` AutoAPI option to
  turn the diagrams on in generated documentation.
* `#183 <https://github.com/readthedocs/sphinx-autoapi/issues/183>`: (Python)
  Added the ``show-inheritance`` AutoAPI option to be able to enable or disable
  the display of a list of base classes in generated documentation about a class.
  Added the ``inherited-members`` AutoAPI option to be able to enable or disable
  the display of members inherited from a base class
  in generated documentation about a class.
* The ``autoapi_include_summaries`` option has been replaced with the
  ``show-module-summary`` AutoAPI option.
  ``autoapi_include_summaries`` will stop working in the next major version.
* Added support for Sphinx 2.4 and 3.0

Bug Fixes
^^^^^^^^^
* `#186 <https://github.com/readthedocs/sphinx-autoapi/issues/186>`: (Python)
  Fixed an exception when there are too many argument type annotations
  in a type comment.
* (Python) args and kwargs type annotations can be read from
  the function type comment.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^
* Tests are now included in the sdist.


v1.2.1 (2019-10-09)
------------------

Bug Fixes
^^^^^^^^^

* (Python) "Invalid desc node" warning no longer raised for autodoc-style
  directives.


v1.2.0 (2019-10-05)
------------------

Features
^^^^^^^^

* (Python) Can read per argument type comments with astroid > 2.2.5.
* (Python) Added autoapidecorator directive with Sphinx >= 2.0.
* (Python) Can use autodoc_docstring_signature with Autodoc-style directives.
* (Python) Added autoapi-skip-member event.
* Made it more clear which file causes an error, when an error occurs.
* Sphinx language domains are now optional dependencies.

Bug Fixes
^^^^^^^^^

* (Python) Forward reference annotations are no longer rendered as strings.
* (Python) autoapifunction directive no longer documents async functions as
  a normal function.
* (Python) Fixed unicode decode errors in some Python 3 situations.
* Documentation more accurately describes what configuration accepts
  relative paths and where they are relative to.


v1.1.0 (2019-06-23)
-------------------

Features
^^^^^^^^

* (Python) Can override ignoring local imports in modules by using __all__.

Bug Fixes
^^^^^^^^^

* (Python) Fixed incorrect formatting of functions and methods.
* Added support for Sphinx 2.1.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* Fixed some dead links in the README.
* Fixed lint virtualenv.


v1.0.0 (2019-04-24)
-------------------

Features
^^^^^^^^

* `#100 <https://github.com/readthedocs/sphinx-autoapi/issues/100>`: (Python) Added support for documenting C extensions via ``.pyi`` stub files.
* Added support for Sphinx 2.0.
* Toned down the API reference index page.
* (Go) Patterns configured in ``autoapi_ignore`` are passed to godocjson.
* New and improved documentation.
* No longer need to set ``autoapi_add_toctree_entry`` to False when ``autoapi_generate_api_docs`` is False.
* `#139 <https://github.com/readthedocs/sphinx-autoapi/issues/139>` Added support for basic type annotations in documentation generation and autodoc-style directives.

Bug Fixes
^^^^^^^^^

* `#159 <https://github.com/readthedocs/sphinx-autoapi/issues/159>`: (Python) Fixed ``UnicodeDecodeError`` on Python 2 when a documenting an attribute that contains binary data.
* (Python) Fixed private submodules displaying when ``private-members`` is turned off.
* Templates no longer produce excessive whitespace.
* (Python) Fixed an error when giving an invalid object to an autodoc-style directive.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* No longer pin the version of black.
* Added missing test environments to travis.


v0.7.1 (2019-02-04)
-------------------

Bug Fixes
^^^^^^^^^

* (Python) Fixed a false warning when importing a local module.


v0.7.0 (2019-01-30)
-------------------

Breaking Changes
^^^^^^^^^^^^^^^^

* Dropped support for Sphinx<1.6.

Features
^^^^^^^^

* Added debug messages about what AutoAPI is doing.

Bug Fixes
^^^^^^^^^

* `#156 <https://github.com/readthedocs/sphinx-autoapi/issues/156>`: (Python) Made import resolution more stable.

    Also capable of giving more detailed warnings.


Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* Code is now formatted using black.
* Removed references to old css and js files.
* Replaced usage of deprecated Sphinx features.
* Reorganised tests to be more pytest-like.


v0.6.2 (2018-11-15)
-------------------

Bug Fixes
^^^^^^^^^

* (Python) Fixed some import chains failing to resolve depending on resolution order.


v0.6.1 (2018-11-14)
-------------------

Bug Fixes
^^^^^^^^^

* (Python) Fixed unicode decoding on Python 3.7.
* (Python) Fixed autodoc directives not documenting anything in submodules or subpackages.
* (Python) Fixed error parsing files with unicode docstrings.
* (Python) Fixed error when documenting something that's imported in more than one place.


Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* (Python) Added Python 3.7 testing.
* Started testing against stable version of Sphinx 1.8.
* Fixed all "no title" warnings during tests.


v0.6.0 (2018-08-20)
-------------------

Breaking Changes
^^^^^^^^^^^^^^^^

* `#152 <https://github.com/readthedocs/sphinx-autoapi/issues/152>`: Removed the ``autoapi_add_api_root_toctree`` option.

    This has been replaced with the ``autoapi_add_toctree_entry`` option.

* `#25 <https://github.com/readthedocs/sphinx-autoapi/issues/25>`: Removed distutils support.
* Removed redundant ``package_dir`` and ``package_data`` options.

Features
^^^^^^^^

* (Python) Added viewcode support for imported members.
* `#146 <https://github.com/readthedocs/sphinx-autoapi/issues/146>`: (Python) No longer documents ``__init__()`` attributes without a docstring.
* `#153 <https://github.com/readthedocs/sphinx-autoapi/issues/153>`: (Python) Can document a public python API.
* `#111 <https://github.com/readthedocs/sphinx-autoapi/issues/111>`: (Python) Can opt to write manual documentation through new autodoc-style directives.
* `#152 <https://github.com/readthedocs/sphinx-autoapi/issues/152>`: Made it easier to remove default index page.

    Also removed autoapi_add_api_root_toctree config option

* `#150 <https://github.com/readthedocs/sphinx-autoapi/issues/150>`: (Python) ``private-members`` also controls private subpackages and submodules.
* (Python) Added support for static and class methods.
* (Python) Methods include ``self`` in their arguments.

    This more closely matches autodoc behaviour.

* `#145 <https://github.com/readthedocs/sphinx-autoapi/issues/145>`: (Python) Added support for detecting Python exceptions.
* (Python) Can control how __init__ docstring is displayed.
* (Python) Added support for viewcode.
* (Python) Source files no longer need to be in ``sys.path``.

Bug Fixes
^^^^^^^^^

* (Python) Fixed linking to builtin bases.
* (Python) Fixed properties being documented more than once when set in ``__init__()``.
* (Python) Fixed nested classes not getting displayed.
* `#148 <https://github.com/readthedocs/sphinx-autoapi/issues/148>`: (Python) Fixed astroid 2.0 compatibility.
* (Python) Fixed filtered classes and attributes getting displayed.
* (Python) Fixed incorrect display of long lists.
* `#125 <https://github.com/readthedocs/sphinx-autoapi/issues/125>`: (Javacript) Fixed running incorrect jsdoc command on Windows.
* `#125 <https://github.com/readthedocs/sphinx-autoapi/issues/125>`: (Python) Support specifying package directories in ``autoapi_dirs``.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* Added Sphinx 1.7 and 1.8.0b1 testing.
* `#120 <https://github.com/readthedocs/sphinx-autoapi/issues/120>`: Updated documentation to remove outdated references.
* Removed old testing dependencies.
* `#143 <https://github.com/readthedocs/sphinx-autoapi/issues/143>`: Removed unnecessary wheel dependency.
