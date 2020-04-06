import io
import os
import shutil
import sys
from mock import patch, Mock, call

import pytest
import sphinx
from sphinx.application import Sphinx
import sphinx.util.logging

from autoapi.mappers.python import (
    PythonModule,
    PythonFunction,
    PythonClass,
    PythonData,
    PythonMethod,
)


@pytest.fixture(scope="class")
def builder():
    cwd = os.getcwd()

    def build(test_dir, confoverrides=None):
        os.chdir("tests/python/{0}".format(test_dir))
        app = Sphinx(
            srcdir=".",
            confdir=".",
            outdir="_build/text",
            doctreedir="_build/.doctrees",
            buildername="text",
            confoverrides=confoverrides,
        )
        app.build(force_all=True)

    yield build

    try:
        shutil.rmtree("_build")
    finally:
        os.chdir(cwd)


class TestSimpleModule(object):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyexample")

    def test_integration(self):
        self.check_integration("_build/text/autoapi/example/index.txt")

    def test_manual_directives(self):
        example_path = "_build/text/manualapi.txt"
        # The manual directives should contain the same information
        self.check_integration(example_path)

        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        if sphinx.version_info >= (2,):
            assert "@example.decorator_okay" in example_file

    def check_integration(self, example_path):
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "class example.Foo" in example_file
        assert "class Meta" in example_file
        assert "attr2" in example_file
        assert "This is the docstring of an instance attribute." in example_file
        assert "method_okay(self, foo=None, bar=None)" in example_file
        assert "method_multiline(self, foo=None, bar=None, baz=None)" in example_file
        assert "method_tricky(self, foo=None, bar=dict(foo=1, bar=2))" in example_file

        # Are constructor arguments from the class docstring parsed?
        assert "Set an attribute" in example_file

        # "self" should not be included in constructor arguments
        assert "Foo(self" not in example_file

        assert not os.path.exists("_build/text/autoapi/method_multiline")

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


@pytest.mark.skipif(
    sys.version_info < (3,), reason="Ellipsis is invalid method contents in Python 2"
)
class TestSimpleStubModule(object):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyiexample")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "class example.Foo" in example_file
        assert "class Meta" in example_file
        assert "Another class var docstring" in example_file
        assert "A class var without a value." in example_file
        assert "method_okay(self, foo=None, bar=None)" in example_file
        assert "method_multiline(self, foo=None, bar=None, baz=None)" in example_file
        assert "method_without_docstring(self)" in example_file

        # Are constructor arguments from the class docstring parsed?
        assert "Set an attribute" in example_file


@pytest.mark.skipif(
    sys.version_info < (3, 6), reason="Annotations are invalid in Python <3.5"
)
class TestPy3Module(object):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py3example")

    def test_annotations(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        assert "max_rating :int = 10" in example_file
        assert "is_valid" in example_file

        assert "ratings" in example_file
        assert "List[int]" in example_file

        assert "Dict[int, str]" in example_file

        assert "start: int" in example_file
        assert "Iterable[int]" in example_file

        assert "List[Union[str, int]]" in example_file

        assert "not_yet_a: A" in example_file
        assert "is_an_a" in example_file
        assert "ClassVar" in example_file

        assert "instance_var" in example_file

        assert "global_a :A" in example_file

    def test_async(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        if sphinx.version_info >= (2, 1):
            assert "async async_method" in example_file
            assert "async example.async_function" in example_file
        else:
            assert "async_method" in example_file
            assert "async_function" in example_file


@pytest.mark.skipif(
    sys.version_info < (3,), reason="Annotations are not supported in astroid<2"
)
class TestAnnotationCommentsModule(object):
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


@pytest.mark.skipif(
    sys.version_info < (3, 8), reason="Positional only arguments need Python >=3.8"
)
class TestPositionalOnlyArgumentsModule(object):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py38positionalparams")

    def test_integration(self):
        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        # Sphinx 3 incorrectly adds default values
        if sphinx.version_info >= (3,):
            assert "f_simple(a, b, /, c, d, *, e=None, f=None)" in example_file

            assert (
                "f_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float = None, f: float = None)"
                in example_file
            )
            assert (
                "f_annotation(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float = None, f: float = None)"
                in example_file
            )
            # Requires unreleased astroid >2.4
            # assert "f_arg_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)" in example_file
            assert (
                "f_no_cd(a: int, b: int, /, *, e: float = None, f: float = None)"
                in example_file
            )
            return

        assert "f_simple(a, b, /, c, d, *, e, f)" in example_file

        assert (
            "f_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
            in example_file
        )
        assert (
            "f_annotation(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
            in example_file
        )
        # Requires unreleased astroid >2.4
        # assert "f_arg_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)" in example_file
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


class TestSimplePackage(object):
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
        assert "method_okay(self, foo=None, bar=None)" in example_foo_file

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


class _CompareInstanceType(object):
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


class TestComplexPackage(object):
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


@pytest.mark.skipif(
    sys.version_info < (3, 3), reason="Implicit namespace not supported in python < 3.3"
)
class TestImplicitNamespacePackage(object):
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
