import io
import os
import shutil

import pytest
import sphinx
from sphinx.application import Sphinx


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
        # The manual directives should contain the same information
        self.check_integration("_build/text/manualapi.txt")

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

        assert "Sphinx AutoAPI Index" in index_file

        assert "Foo" in index_file
        assert "Meta" in index_file

    def test_napoleon_integration_not_loaded(self, builder):

        example_path = "_build/text/autoapi/example/index.txt"
        with io.open(example_path, encoding="utf8") as example_handle:
            example_file = example_handle.read()

        # Check that docstrings are not transformed without napoleon loaded
        assert "Args" in example_file

        assert "Returns" in example_file


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

        assert "Sphinx AutoAPI Index" in index_file
        assert "example.foo" in index_file
        assert "Foo" in index_file
        assert "module_level_method" in index_file


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
