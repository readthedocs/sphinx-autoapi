import io
import os
import pathlib
import re
import shutil
import sys
from unittest.mock import patch, Mock, call

import pytest
import sphinx
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
import sphinx.util.logging

from autoapi.mappers.python import (
    PythonModule,
    PythonFunction,
    PythonClass,
    PythonData,
    PythonMethod,
)
import autoapi.settings


def rebuild(confoverrides=None, confdir=".", **kwargs):
    app = Sphinx(
        srcdir=".",
        confdir=confdir,
        outdir="_build/text",
        doctreedir="_build/.doctrees",
        buildername="text",
        confoverrides=confoverrides,
        **kwargs
    )
    app.build()


@pytest.fixture(scope="class")
def builder():
    cwd = os.getcwd()

    def build(test_dir, confoverrides=None, **kwargs):
        os.chdir("tests/python/{0}".format(test_dir))
        rebuild(confoverrides=confoverrides, **kwargs)

    yield build

    try:
        shutil.rmtree("_build")
    finally:
        os.chdir(cwd)


class TestSimpleModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={"suppress_warnings": ["app"]},
        )

    def test_integration(self):
        self.check_integration("_build/text/autoapi/example/index.txt")

    def test_manual_directives(self):
        example_path = "_build/text/manualapi.txt"
        # The manual directives should contain the same information
        self.check_integration(example_path)

        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "@example.decorator_okay" in example_file

    def check_integration(self, example_path):
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "class example.Foo" in example_file
        assert "class Meta" in example_file
        assert "attr2" in example_file
        assert "This is the docstring of an instance attribute." in example_file
        assert "method_okay(foo=None, bar=None)" in example_file
        assert "method_multiline(foo=None, bar=None, baz=None)" in example_file
        assert "method_tricky(foo=None, bar=dict(foo=1, bar=2))" in example_file

        # Are constructor arguments from the class docstring parsed?
        assert "Set an attribute" in example_file

        # "self" should not be included in constructor arguments
        assert "Foo(self" not in example_file

        # Overridden methods without their own docstring
        # should inherit the parent's docstring
        assert example_file.count("This method should parse okay") == 2

        assert not os.path.exists("_build/text/autoapi/method_multiline")

        # Inherited constructor docstrings should be included in a merged
        # (autoapi_python_class_content="both") class docstring only once.
        assert example_file.count("One __init__.") == 3

        index_path = "_build/text/index.txt"
        with io.open(index_path, encoding="utf8") as index_handle:
            index_file = index_handle.read()

        assert "API Reference" in index_file

        assert "Foo" in index_file
        assert "Meta" in index_file

    def test_napoleon_integration_not_loaded(self, builder):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        # Check that docstrings are not transformed without napoleon loaded
        assert "Args" in example_file

        assert "Returns" in example_file

    def test_show_inheritance(self, builder):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "Bases:" in example_file

    def test_long_signature(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        summary_row = """
+------------+--------------------------------------------------------------------------------------------+
| "fn_with_  | A function with a long signature.                                                          |
| long_sig"  |                                                                                            |
| (this, *[, |                                                                                            |
| function,  |                                                                                            |
| has,       |                                                                                            |
| quite])    |                                                                                            |
+------------+--------------------------------------------------------------------------------------------+
        """.strip()
        assert summary_row in example_file

        # Check length of truncated signature
        parts = []
        for line in summary_row.splitlines()[1:-1]:
            part = line.split("|")[1].strip()
            if part.endswith(","):
                part += " "
            parts.append(part)
        sig_summary = "".join(parts)
        assert len(sig_summary) <= 60


class TestMovedConfPy(TestSimpleModule):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pymovedconfpy",
            confdir="confpy",
            warningiserror=True,
            confoverrides={"suppress_warnings": ["app"]},
        )


class TestSimpleModuleDifferentPrimaryDomain:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={
                "autoapi_options": [
                    "members",
                    "undoc-members",
                    "private-members",
                    "special-members",
                    "imported-members",
                ],
                "primary_domain": "cpp",
                "suppress_warnings": ["app"],
            },
        )

    def test_success(self):
        pass


class TestSimpleStubModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyiexample")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        # Are pyi files preferred
        assert "DoNotFindThis" not in example_file

        assert "class example.Foo" in example_file
        assert "class Meta" in example_file
        assert "Another class var docstring" in example_file
        assert "A class var without a value." in example_file
        assert "method_okay(foo=None, bar=None)" in example_file
        assert "method_multiline(foo=None, bar=None, baz=None)" in example_file
        assert "method_without_docstring()" in example_file

        # Are constructor arguments from the class docstring parsed?
        assert "Set an attribute" in example_file


class TestSimpleStubModuleNotPreferred:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyiexample2")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        # Are py files preferred
        assert "DoNotFindThis" not in example_file

        assert "Foo" in example_file


class TestPy3Module:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py3example")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "Initialize self" not in example_file
        assert "a new type" not in example_file

    def test_annotations(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "software = sphinx" in example_file
        assert "code_snippet = Multiline-String" in example_file

        assert "max_rating :int = 10" in example_file
        assert "is_valid" in example_file

        assert "ratings" in example_file
        assert "List[int]" in example_file

        assert "Dict[int, str]" in example_file

        assert "start: int" in example_file
        assert "Iterable[int]" in example_file

        assert "List[Union[str, int]]" in example_file

        assert "not_yet_a: A" in example_file
        assert "imported: example2.B" in example_file
        assert "-> example2.B" in example_file

        assert "is_an_a" in example_file
        assert "ClassVar" in example_file

        assert "instance_var" in example_file

        assert "global_a :A" in example_file

        assert "my_method() -> str" in example_file

        assert "class example.SomeMetaclass" in example_file

    def test_overload(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "overloaded_func(a: float" in example_file
        assert "overloaded_func(a: str" in example_file
        assert "overloaded_func(a: Union" not in example_file
        assert "Overloaded function" in example_file

        assert "overloaded_method(a: float" in example_file
        assert "overloaded_method(a: str" in example_file
        assert "overloaded_method(a: Union" not in example_file
        assert "Overloaded method" in example_file

        assert "overloaded_class_method(a: float" in example_file
        assert "overloaded_class_method(a: str" in example_file
        assert "overloaded_class_method(a: Union" not in example_file
        assert "Overloaded method" in example_file

        assert "undoc_overloaded_func" in example_file
        assert "undoc_overloaded_method" in example_file

        assert "C(a: int" in example_file
        assert "C(a: float" in example_file
        assert "C(a: str" not in example_file
        assert "C(self, a: int" not in example_file
        assert "C(self, a: float" not in example_file
        assert "C(self, a: str" not in example_file

    def test_async(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "async async_method" in example_file
        assert "async example.async_function" in example_file


def test_py3_hiding_undoc_overloaded_members(builder):
    confoverrides = {"autoapi_options": ["members", "special-members"]}
    builder("py3example", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "overloaded_func" in example_file
    assert "overloaded_method" in example_file
    assert "undoc_overloaded_func" not in example_file
    assert "undoc_overloaded_method" not in example_file


class TestAnnotationCommentsModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyannotationcommentsexample")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "max_rating :int = 10" in example_file

        assert "ratings" in example_file
        assert "List[int]" in example_file

        assert "Dict[int, str]" in example_file

        # When astroid>2.2.5
        # assert "start: int" in example_file
        # assert "end: int" in example_file
        assert "Iterable[int]" in example_file

        assert "List[Union[str, int]]" in example_file

        assert "not_yet_a: A" in example_file
        assert "is_an_a" in example_file
        assert "ClassVar" in example_file

        assert "instance_var" in example_file

        assert "global_a :A" in example_file

        assert "class example.B(a: str)" in example_file
        assert "method(b: list)" in example_file
        assert "classmethod class_method(c: int)" in example_file
        assert "static static_method(d: float)" in example_file


@pytest.mark.skipif(
    sys.version_info < (3, 8), reason="Positional only arguments need Python >=3.8"
)
class TestPositionalOnlyArgumentsModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py38positionalparams")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "f_simple(a, b, /, c, d, *, e, f)" in example_file

        assert (
            "f_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
            in example_file
        )
        assert (
            "f_annotation(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
            in example_file
        )
        assert (
            "f_arg_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
            in example_file
        )
        assert "f_no_cd(a: int, b: int, /, *, e: float, f: float)" in example_file


def test_napoleon_integration_loaded(builder):
    confoverrides = {
        "extensions": ["autoapi.extension", "sphinx.ext.autodoc", "sphinx.ext.napoleon"]
    }

    builder("pyexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "Parameters" in example_file

    assert "Return type" in example_file

    assert "Args" not in example_file


class TestSimplePackage:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pypackageexample")

    def test_integration_with_package(self):

        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "example.foo" in example_file
        assert "example.module_level_method(foo, bar)" in example_file

        example_foo_path = "_build/text/autoapi/example/foo/index.txt"
        with io.open(example_foo_path, encoding="utf8") as example_foo_handle:
            example_foo_file = example_foo_handle.read()

        assert "class example.foo.Foo" in example_foo_file
        assert "method_okay(foo=None, bar=None)" in example_foo_file

        index_path = "_build/text/index.txt"
        with io.open(index_path, encoding="utf8") as index_handle:
            index_file = index_handle.read()

        assert "API Reference" in index_file
        assert "example.foo" in index_file
        assert "Foo" in index_file
        assert "module_level_method" in index_file


def test_simple_no_false_warnings(builder, caplog):
    logger = sphinx.util.logging.getLogger("autoapi")
    logger.logger.addHandler(caplog.handler)
    builder("pypackageexample")

    assert "Cannot resolve" not in caplog.text


def _test_class_content(builder, class_content):
    confoverrides = {"autoapi_python_class_content": class_content}

    builder("pyexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

        if class_content == "init":
            assert "Can we parse arguments" not in example_file
        else:
            assert "Can we parse arguments" in example_file

        if class_content not in ("both", "init"):
            assert "Constructor docstring" not in example_file
        else:
            assert "Constructor docstring" in example_file


def test_class_class_content(builder):
    _test_class_content(builder, "class")


def test_both_class_content(builder):
    _test_class_content(builder, "both")


def test_init_class_content(builder):
    _test_class_content(builder, "init")


def test_hiding_private_members(builder):
    confoverrides = {"autoapi_options": ["members", "undoc-members", "special-members"]}
    builder("pypackageexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "private" not in example_file

    private_path = "_build/text/autoapi/example/_private_module/index.txt"
    with io.open(private_path, encoding="utf8") as private_handle:
        private_file = private_handle.read()

    assert "public_method" in private_file


def test_hiding_inheritance(builder):
    confoverrides = {"autoapi_options": ["members", "undoc-members", "special-members"]}
    builder("pyexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "Bases:" not in example_file


def test_hiding_imported_members(builder):
    confoverrides = {"autoapi_options": ["members", "undoc-members"]}
    builder("pypackagecomplex", confoverrides=confoverrides)

    subpackage_path = "_build/text/autoapi/complex/subpackage/index.txt"
    with io.open(subpackage_path, encoding="utf8") as subpackage_handle:
        subpackage_file = subpackage_handle.read()

    assert "Part of a public resolution chain." not in subpackage_file

    package_path = "_build/text/autoapi/complex/index.txt"
    with io.open(package_path, encoding="utf8") as package_handle:
        package_file = package_handle.read()

    assert "Part of a public resolution chain." not in package_file

    submodule_path = "_build/text/autoapi/complex/subpackage/submodule/index.txt"
    with io.open(submodule_path, encoding="utf8") as submodule_handle:
        submodule_file = submodule_handle.read()

    assert "A private function made public by import." not in submodule_file


def test_inherited_members(builder):
    confoverrides = {
        "autoapi_options": ["members", "inherited-members", "undoc-members"]
    }
    builder("pyexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "class example.Bar" in example_file
    i = example_file.index("class example.Bar")
    assert "method_okay" in example_file[i:]


def test_skipping_members(builder):
    builder("pyskipexample")

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "foo doc" not in example_file
    assert "bar doc" not in example_file
    assert "bar m doc" not in example_file
    assert "baf doc" in example_file
    assert "baf m doc" not in example_file
    assert "baz doc" not in example_file
    assert "not ignored" in example_file


@pytest.mark.parametrize(
    "value,order",
    [
        ("bysource", [".Foo", ".decorator_okay", ".Bar"]),
        ("alphabetical", [".Bar", ".Foo", ".decorator_okay"]),
        ("groupwise", [".Bar", ".Foo", ".decorator_okay"]),
    ],
)
def test_order_members(builder, value, order):
    confoverrides = {"autoapi_member_order": value}
    builder("pyexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    indexes = [example_file.index(name) for name in order]
    assert indexes == sorted(indexes)


class _CompareInstanceType:
    def __init__(self, type_):
        self.type = type_

    def __eq__(self, other):
        return self.type is type(other)

    def __repr__(self):
        return "<expect type {}>".format(self.type.__name__)


def test_skip_members_hook(builder):
    emit_firstresult_patch = Mock(name="emit_firstresult_patch", return_value=False)
    with patch("sphinx.application.Sphinx.emit_firstresult", emit_firstresult_patch):
        builder("pyskipexample")

    options = ["members", "undoc-members", "special-members"]

    mock_calls = [
        call(
            "autoapi-skip-member",
            "module",
            "example",
            _CompareInstanceType(PythonModule),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "function",
            "example.foo",
            _CompareInstanceType(PythonFunction),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "class",
            "example.Bar",
            _CompareInstanceType(PythonClass),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "class",
            "example.Baf",
            _CompareInstanceType(PythonClass),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "data",
            "example.baz",
            _CompareInstanceType(PythonData),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "data",
            "example.anchor",
            _CompareInstanceType(PythonData),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "method",
            "example.Bar.m",
            _CompareInstanceType(PythonMethod),
            False,
            options,
        ),
        call(
            "autoapi-skip-member",
            "method",
            "example.Baf.m",
            _CompareInstanceType(PythonMethod),
            False,
            options,
        ),
    ]
    for mock_call in mock_calls:
        assert mock_call in emit_firstresult_patch.mock_calls


class TestComplexPackage:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pypackagecomplex")

    def test_public_chain_resolves(self):
        submodule_path = "_build/text/autoapi/complex/subpackage/submodule/index.txt"
        with io.open(submodule_path, encoding="utf8") as submodule_handle:
            submodule_file = submodule_handle.read()

        assert "Part of a public resolution chain." in submodule_file

        subpackage_path = "_build/text/autoapi/complex/subpackage/index.txt"
        with io.open(subpackage_path, encoding="utf8") as subpackage_handle:
            subpackage_file = subpackage_handle.read()

        assert "Part of a public resolution chain." in subpackage_file

        package_path = "_build/text/autoapi/complex/index.txt"
        with io.open(package_path, encoding="utf8") as package_handle:
            package_file = package_handle.read()

        assert "Part of a public resolution chain." in package_file

    def test_private_made_public(self):
        submodule_path = "_build/text/autoapi/complex/subpackage/submodule/index.txt"
        with io.open(submodule_path, encoding="utf8") as submodule_handle:
            submodule_file = submodule_handle.read()

        assert "A private function made public by import." in submodule_file

    def test_multiple_import_locations(self):
        submodule_path = "_build/text/autoapi/complex/subpackage/submodule/index.txt"
        with io.open(submodule_path, encoding="utf8") as submodule_handle:
            submodule_file = submodule_handle.read()

        assert "A public function imported in multiple places." in submodule_file

        subpackage_path = "_build/text/autoapi/complex/subpackage/index.txt"
        with io.open(subpackage_path, encoding="utf8") as subpackage_handle:
            subpackage_file = subpackage_handle.read()

        assert "A public function imported in multiple places." in subpackage_file

        package_path = "_build/text/autoapi/complex/index.txt"
        with io.open(package_path, encoding="utf8") as package_handle:
            package_file = package_handle.read()

        assert "A public function imported in multiple places." in package_file

    def test_simple_wildcard_imports(self):
        wildcard_path = "_build/text/autoapi/complex/wildcard/index.txt"
        with io.open(wildcard_path, encoding="utf8") as wildcard_handle:
            wildcard_file = wildcard_handle.read()

        assert "public_chain" in wildcard_file
        assert "now_public_function" in wildcard_file
        assert "public_multiple_imports" in wildcard_file
        assert "module_level_method" in wildcard_file

    def test_wildcard_chain(self):
        wildcard_path = "_build/text/autoapi/complex/wildchain/index.txt"
        with io.open(wildcard_path, encoding="utf8") as wildcard_handle:
            wildcard_file = wildcard_handle.read()

        assert "public_chain" in wildcard_file
        assert "module_level_method" in wildcard_file

    def test_wildcard_all_imports(self):
        wildcard_path = "_build/text/autoapi/complex/wildall/index.txt"
        with io.open(wildcard_path, encoding="utf8") as wildcard_handle:
            wildcard_file = wildcard_handle.read()

        assert "not_all" not in wildcard_file
        assert "NotAllClass" not in wildcard_file
        assert "does_not_exist" not in wildcard_file
        assert "SimpleClass" in wildcard_file
        assert "simple_function" in wildcard_file
        assert "public_chain" in wildcard_file
        assert "module_level_method" in wildcard_file

    def test_no_imports_in_module_with_all(self):
        foo_path = "_build/text/autoapi/complex/foo/index.txt"
        with io.open(foo_path, encoding="utf8") as foo_handle:
            foo_file = foo_handle.read()

        assert "module_level_method" not in foo_file

    def test_all_overrides_import_in_module_with_all(self):
        foo_path = "_build/text/autoapi/complex/foo/index.txt"
        with io.open(foo_path, encoding="utf8") as foo_handle:
            foo_file = foo_handle.read()

        assert "PublicClass" in foo_file

    def test_parses_unicode_file(self):
        foo_path = "_build/text/autoapi/complex/unicode_data/index.txt"
        with io.open(foo_path, encoding="utf8") as foo_handle:
            foo_file = foo_handle.read()

        assert "unicode_str" in foo_file


class TestComplexPackageParallel:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pypackagecomplex", parallel=2)

    def test_success(self):
        pass


def test_caching(builder):
    mtimes = (0, 0)

    def record_mtime():
        nonlocal mtimes
        mtime = 0
        for root, _, files in os.walk("_build/text/autoapi"):
            for name in files:
                this_mtime = os.path.getmtime(os.path.join(root, name))
                mtime = max(mtime, this_mtime)

        mtimes = (*mtimes[1:], mtime)

    builder("pypackagecomplex", confoverrides={"autoapi_keep_files": True})
    record_mtime()

    rebuild(confoverrides={"autoapi_keep_files": True})
    record_mtime()

    assert mtimes[1] == mtimes[0]

    # Check that adding a file rebuilds the docs
    extra_file = "complex/new.py"
    with open(extra_file, "w") as out_f:
        out_f.write("\n")

    try:
        rebuild(confoverrides={"autoapi_keep_files": True})
    finally:
        os.remove(extra_file)

    record_mtime()
    assert mtimes[1] != mtimes[0]

    # Removing a file also rebuilds the docs
    rebuild(confoverrides={"autoapi_keep_files": True})
    record_mtime()
    assert mtimes[1] != mtimes[0]

    # Changing not keeping files always builds
    rebuild()
    record_mtime()
    assert mtimes[1] != mtimes[0]


class TestImplicitNamespacePackage:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py3implicitnamespace")

    def test_sibling_import_from_namespace(self):
        example_path = "_build/text/autoapi/namespace/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "namespace.example.first_method" in example_file

    def test_sub_sibling_import_from_namespace(self):
        example_path = "_build/text/autoapi/namespace/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "namespace.example.second_sub_method" in example_file


def test_custom_jinja_filters(builder, tmp_path):
    py_templates = tmp_path / "python"
    py_templates.mkdir()
    orig_py_templates = pathlib.Path(autoapi.settings.TEMPLATE_DIR) / "python"
    orig_template = (orig_py_templates / "class.rst").read_text()
    (py_templates / "class.rst").write_text(
        orig_template.replace("obj.docstring", "obj.docstring|prepare_docstring")
    )

    confoverrides = {
        "autoapi_prepare_jinja_env": (
            lambda jinja_env: jinja_env.filters.update(
                {
                    "prepare_docstring": (
                        lambda docstring: "This is using custom filters."
                    )
                }
            )
        ),
        "autoapi_template_dir": str(tmp_path),
    }
    builder("pyexample", confoverrides=confoverrides)

    example_path = "_build/text/autoapi/example/index.txt"
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    assert "This is using custom filters." in example_file


def test_string_module_attributes(builder):
    """Test toggle for multi-line string attribute values (GitHub #267)."""
    keep_rst = {
        "autoapi_keep_files": True,
        "autoapi_root": "_build/autoapi",  # Preserve RST files under _build for cleanup
    }
    builder("py3example", confoverrides=keep_rst)

    example_path = os.path.join(keep_rst["autoapi_root"], "example", "index.rst")
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    code_snippet_contents = [
        ".. py:data:: code_snippet",
        "   :annotation: = Multiline-String",
        "",
        "    .. raw:: html",
        "",
        "        <details><summary>Show Value</summary>",
        "",
        "    .. code-block:: text",
        "        :linenos:",
        "",
        "        ",  # <--- Line array monstrosity to preserve these leading spaces
        "        # -*- coding: utf-8 -*-",
        "        from __future__ import absolute_import, division, print_function, unicode_literals",
        "        # from future.builtins.disabled import *",
        "        # from builtins import *",
        "",
        """        print("chunky o'block")""",
        "",
        "",
        "    .. raw:: html",
        "",
        "        </details>",
    ]
    assert "\n".join(code_snippet_contents) in example_file


class TestAutodocTypehintsPackage:
    """Test integrations with the autodoc.typehints extension."""

    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyautodoc_typehints")

    def test_renders_typehint(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "(*int*)" in example_file

    def test_renders_typehint_in_second_module(self):
        example2_path = "_build/text/autoapi/example2/index.txt"
        with io.open(example2_path, encoding="utf8") as example2_handle:
            example2_file = example2_handle.read()

        assert "(*int*)" in example2_file


def test_no_files_found(builder):
    """Test that building does not fail when no sources files are found."""
    with pytest.raises(ExtensionError) as exc_info:
        builder("pyemptyexample")

    assert os.path.dirname(__file__) in str(exc_info.value)


class TestMdSource:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={"source_suffix": ["md"]},
        )
