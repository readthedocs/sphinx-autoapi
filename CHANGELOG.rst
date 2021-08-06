Changelog
=========

Versions follow `Semantic Versioning <https://semver.org/>`_ (``<major>.<minor>.<patch>``).

v1.8.3 (2021-07-31)
-------------------

Bug Fixes
^^^^^^^^^
* `#299 <https://github.com/readthedocs/sphinx-autoapi/issues/299>`: (Python)
  Fixed incorrect indentation in generated documentation when a class with no
  constructor has a summary line spanning multiple lines.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^
* Fixed broken link to Jinja objects.inv.


v1.8.2 (2021-07-26)
-------------------

Bug Fixes
^^^^^^^^^

* Fixed error when parsing a class with no constructor.
* `#293 <https://github.com/readthedocs/sphinx-autoapi/issues/293>`:
  Fixed failure to build out of source conf.py files.
  Configuration values using relative values are now relative to the source directory
  instead of relative to the conf.py file.
* `#289 <https://github.com/readthedocs/sphinx-autoapi/issues/289>`: (Python)
  Fixed AttributeError using inheritance diagrams on a module with plain imports.
* `#292 <https://github.com/readthedocs/sphinx-autoapi/issues/292>`:
  Explicitly use the domain for generated directives.


v1.8.1 (2021-04-24)
-------------------

Bug Fixes
^^^^^^^^^

* `#273 <https://github.com/readthedocs/sphinx-autoapi/issues/273>`:
  Fixed type annotations being shown for only a single module.


v1.8.0 (2021-04-12)
-------------------

Features
^^^^^^^^

* Expandable value for multi-line string attributes.
* `#265 <https://github.com/readthedocs/sphinx-autoapi/issues/265>`:
  Can resolve the qualified paths of parameters to generics.
* `#275 <https://github.com/readthedocs/sphinx-autoapi/issues/275>`:
  Warnings have been categorised and can be suppressed through ``suppress_warnings``.
* `#280 <https://github.com/readthedocs/sphinx-autoapi/issues/280>`:
  Data attributes are documentated in module summaries.

Bug Fixes
^^^^^^^^^

* `#273 <https://github.com/readthedocs/sphinx-autoapi/issues/273>`:
  Fixed setting ``autodoc_typehints`` to ``none`` or ``description``
  not turning off signature type hints.
  ``autodoc_typehints`` integration is consisidered experimental until
  the extension properly supports overload functions.
* `#261 <https://github.com/readthedocs/sphinx-autoapi/issues/261>`:
  Fixed data annotations causing pickle or deepcopy errors.
* Documentation can be generated when multiple source directories
  share a single ``conf.py`` file.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* Fixed ``DeprecationWarning`` for invalid escape sequence ``\s`` in tests.
* Fixed ``FutureWarning`` for ``Node.traverse()`` becoming an iterator instead of list.
* New example implementation of ``autoapi-skip-member`` Sphinx event.
* Can run tests with tox 4.
* Updated packaging to use PEP-517.
* All unittest style tests have been converted to pytest style tests.
* An exception raised by docfx is raised directly instead of wrapping it.
* Started using Github Actions for continuous integration.


V1.7.0 (2021-01-31)
-------------------

Features
^^^^^^^^

* The fully qualified path of objects are included type annotations
  so that Sphinx can link to them.
* Added support for Sphinx 3.3. and 3.4.
* `#240 <https://github.com/readthedocs/sphinx-autoapi/issues/240>`:
  The docstrings of ``object.__init__``, ``object.__new__``,
  ``type.__init__``, and ``type.__new__`` are not inherited.

Bug Fixes
^^^^^^^^^

* `#260 <https://github.com/readthedocs/sphinx-autoapi/issues/260>`:
  The overload signatures of ``__init__`` methods are documented.


V1.6.0 (2021-01-20)
-------------------

Breaking Changes
^^^^^^^^^^^^^^^^

* Dropped support for Python 2 and Sphinx 1.x/2.x.
  Python 2 source code can still be parsed.

Features
^^^^^^^^

* (Python) Added support for using type hints as parameter types and return types
  via the ``sphinx.ext.autodoc.typehints`` extension.
* `#191 <https://github.com/readthedocs/sphinx-autoapi/issues/191>`:
  Basic incremental build support is enabled ``autoapi_keep_files`` is enabled.
  Providing none of the source files have changed,
  AutoAPI will skip parsing the source code and regenerating the API documentation.
* `#200 <https://github.com/readthedocs/sphinx-autoapi/issues/200>`:
  Can pass a callback that edits the Jinja Environment object before
  template rendering begins.
  This allows custom filters, tests, and globals to be added to the environment.
* Added support for Python 3.9.

Bug Fixes
^^^^^^^^^

* `#246 <https://github.com/readthedocs/sphinx-autoapi/issues/246>`: (Python)
  Fixed TypeError when parsing a class that inherits from ``type``.
* `#244 <https://github.com/readthedocs/sphinx-autoapi/issues/244>`:
  Fixed an unnecessary deprecation warning being raised when running
  sphinx-build from the same directory as conf.py.
* (Python) Fixed properties documented by Autodoc directives geting documented as methods.


V1.5.1 (2020-10-01)
-------------------

Bug Fixes
^^^^^^^^^

* Fixed AttributeError when generating an inheritance diagram for a module.


V1.5.0 (2020-08-31)
-------------------

This will be the last minor version to support Python 2 and Sphinx 1.x/2.x.

Features
^^^^^^^^

* `#222 <https://github.com/readthedocs/sphinx-autoapi/issues/222>`:
  Declare the extension as parallel unsafe.
* `#217 <https://github.com/readthedocs/sphinx-autoapi/issues/217>`: (Python)
  All overload signatures are documented.
* `#243 <https://github.com/readthedocs/sphinx-autoapi/issues/243>`:
  Files are found in order of preference according to ``autoapi_file_patterns``.
* Added support for Sphinx 3.2.

Bug Fixes
^^^^^^^^^

* `#219 <https://github.com/readthedocs/sphinx-autoapi/issues/219>`: (Python)
  Fixed return types not showing for methods.
* (Python) Fixed incorrect formatting of properties on generated method directives.
* Fixed every toctree entry getting added as a new list.
* `#234 <https://github.com/readthedocs/sphinx-autoapi/issues/234>`:
  Fixed only some entries getting added to the toctree.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* autoapisummary directive inherits from autosummary for future stability.


v1.4.0 (2020-06-07)
-------------------

Features
^^^^^^^^

* `#197 <https://github.com/readthedocs/sphinx-autoapi/issues/197>`: Added
  ``autoapi.__version__`` and ``autoapi.__version_info__`` attributes
  for accessing version information.
* `#201 <https://github.com/readthedocs/sphinx-autoapi/issues/201>`: (Python)
  Added the ``autoapi_member_order`` option to allow the order that members
  are documentated to be configurable.
* `#203 <https://github.com/readthedocs/sphinx-autoapi/issues/203>`: (Python)
  A class without a docstring inherits one from its parent.
  A methods without a docstring inherits one from the method that it overrides.
* `#204 <https://github.com/readthedocs/sphinx-autoapi/issues/204>`: (Python)
  Added the ``imported-members`` AutoAPI option to be able to enable or disable
  documenting objects imported from the same top-level package or module
  without needing to override templates.

Bug Fixes
^^^^^^^^^

* `#198 <https://github.com/readthedocs/sphinx-autoapi/issues/198>`:
  Documentation describes the required layout for template override directories.
* `#195 <https://github.com/readthedocs/sphinx-autoapi/issues/195>`: (Python)
  Fixed incorrect formatting when ``show-inheritance-diagram``
  and ``private-members`` are turned on.
* `#193 <https://github.com/readthedocs/sphinx-autoapi/issues/193>` and
  `#208 <https://github.com/readthedocs/sphinx-autoapi/issues/208>`: (Python)
  Inheritance diagrams can follow imports to find classes to document.
* `#213 <https://github.com/readthedocs/sphinx-autoapi/issues/213>`: (Python)
  Fixed module summary never showing.

Trivial/Internal Changes
^^^^^^^^^^^^^^^^^^^^^^^^

* black shows diffs by default
* `#207 <https://github.com/readthedocs/sphinx-autoapi/issues/207>`:
  Fixed a typo in the code of the golang tutorial.


v1.3.0 (2020-04-05)
-------------------

Breaking Changes
^^^^^^^^^^^^^^^^

* Dropped support for Python 3.4 and 3.5.

Features
^^^^^^^^

* `#151 <https://github.com/readthedocs/sphinx-autoapi/issues/151>`: (Python)
  Added the ``autoapi_python_use_implicit_namespaces`` option to allow
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
-------------------

Bug Fixes
^^^^^^^^^

* (Python) "Invalid desc node" warning no longer raised for autodoc-style
  directives.


v1.2.0 (2019-10-05)
-------------------

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

* `#100 <https://github.com/readthedocs/sphinx-autoapi/issues/100>`: (Python)
  Added support for documenting C extensions via ``.pyi`` stub files.
* Added support for Sphinx 2.0.
* Toned down the API reference index page.
* (Go) Patterns configured in ``autoapi_ignore`` are passed to godocjson.
* New and improved documentation.
* No longer need to set ``autoapi_add_toctree_entry`` to False when ``autoapi_generate_api_docs`` is False.
* `#139 <https://github.com/readthedocs/sphinx-autoapi/issues/139>`
  Added support for basic type annotations in documentation generation and autodoc-style directives.

Bug Fixes
^^^^^^^^^

* `#159 <https://github.com/readthedocs/sphinx-autoapi/issues/159>`: (Python)
  Fixed ``UnicodeDecodeError`` on Python 2 when a documenting an attribute that contains binary data.
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
