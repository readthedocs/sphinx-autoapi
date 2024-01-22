import io
import os
import pathlib
import sys
from unittest.mock import Mock, call

import autoapi.settings
from autoapi.mappers.python import (
    PythonClass,
    PythonData,
    PythonFunction,
    PythonMethod,
    PythonModule,
)
from packaging import version
import pytest
import sphinx
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
import sphinx.util.logging

sphinx_version = version.parse(sphinx.__version__).release


class TestSimpleModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={"exclude_patterns": ["manualapi.rst"]},
        )

    def test_integration(self, parse):
        self.check_integration(parse, "_build/html/autoapi/example/index.html")

        index_file = parse("_build/html/index.html")

        toctree = index_file.select("li > a")
        assert any(item.text == "API Reference" for item in toctree)

    def check_integration(self, parse, example_path):
        example_file = parse(example_path)
        foo_sig = example_file.find(id="example.Foo")
        assert foo_sig
        assert foo_sig.find(class_="sig-name").text == "Foo"
        assert foo_sig.find(class_="sig-param").text == "attr"

        # Check that nested classes are documented
        foo = foo_sig.parent
        assert foo.find(id="example.Foo.Meta")

        # Check that class attributes are documented
        attr2 = foo.find(id="example.Foo.attr2")
        assert "attr2" in attr2.text
        # Check that attribute docstrings are used
        assert attr2.parent.find("dd").text.startswith(
            "This is the docstring of an instance attribute."
        )

        method_okay = foo.find(id="example.Foo.method_okay")
        assert method_okay
        args = method_okay.find_all(class_="sig-param")
        assert len(args) == 2
        assert args[0].text == "foo=None"
        assert args[1].text == "bar=None"

        method_multiline = foo.find(id="example.Foo.method_multiline")
        assert method_multiline
        args = method_multiline.find_all(class_="sig-param")
        assert len(args) == 3
        assert args[0].text == "foo=None"
        assert args[1].text == "bar=None"
        assert args[2].text == "baz=None"

        method_tricky = foo.find(id="example.Foo.method_tricky")
        assert method_tricky
        args = method_tricky.find_all(class_="sig-param")
        assert len(args) == 2
        assert args[0].text == "foo=None"
        assert args[1].text == "bar=dict(foo=1, bar=2)"

        # Are constructor arguments from the class docstring parsed?
        init_args = foo.parent.find_next(class_="field-list")
        assert "Set an attribute" in init_args.text

        # "self" should not be included in constructor arguments
        assert len(foo_sig.find_all(class_="sig-param")) == 1

        property_simple = foo.find(id="example.Foo.property_simple")
        assert property_simple
        assert (
            property_simple.parent.find("dd").text.strip()
            == "This property should parse okay."
        )

        # Overridden methods without their own docstring
        # should inherit the parent's docstring
        bar_method_okay = example_file.find(id="example.Bar.method_okay")
        assert (
            bar_method_okay.parent.find("dd").text.strip()
            == "This method should parse okay"
        )

        assert not os.path.exists("_build/html/autoapi/method_multiline")

        # Inherited constructor docstrings should be included in a merged
        # (autoapi_python_class_content="both") class docstring only once.
        two = example_file.find(id="example.Two")
        assert two.parent.find("dd").text.count("One __init__") == 1

        # Tuples should be rendered as tuples, not lists
        a_tuple = example_file.find(id="example.A_TUPLE")
        assert a_tuple.find(class_="property").text.endswith("('a', 'b')")
        # Lists should be rendered as lists, not tuples
        a_list = example_file.find(id="example.A_LIST")
        assert a_list.find(class_="property").text.endswith("['c', 'd']")

        # Assigning a class level attribute at the module level
        # should not get documented as a module level attribute.
        assert "dinglebop" not in example_file.text

        index_file = parse("_build/html/index.html")

        toctree = index_file.select("li > a")
        assert any(item.text == "Foo" for item in toctree)
        assert any(item.text == "Foo.Meta" for item in toctree)

    def test_napoleon_integration_not_loaded(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        # Check that docstrings are not transformed without napoleon loaded
        method_google = example_file.find(id="example.Foo.method_google_docs")
        assert "Args" in method_google.parent.find("dd").text
        assert "Returns" in method_google.parent.find("dd").text

    def test_show_inheritance(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        foo = example_file.find(id="example.Foo")
        foo_docstring = foo.parent.find("dd").contents[0]
        assert foo_docstring.text.startswith("Bases:")

    def test_long_signature(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        summary_row = example_file.find_all(class_="autosummary")[-1].find_all("tr")[-1]
        assert summary_row
        cells = summary_row.find_all("td")
        assert (
            cells[0].text.replace("\xa0", " ")
            == "fn_with_long_sig(this, *[, function, has, quite])"
        )
        assert cells[1].text.strip() == "A function with a long signature."


class TestSimpleModuleManual:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={
                "autoapi_generate_api_docs": False,
                "autoapi_add_toctree_entry": False,
            },
        )

    def test_manual_directives(self, parse):
        example_file = parse("_build/html/manualapi.html")
        assert example_file.find(id="example.decorator_okay")


class TestMovedConfPy(TestSimpleModule):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pymovedconfpy",
            confdir="confpy",
            warningiserror=True,
            confoverrides={"exclude_patterns": ["manualapi.rst"]},
        )


class TestSimpleModuleDifferentPrimaryDomain(TestSimpleModule):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={
                "exclude_patterns": ["manualapi.rst"],
                "primary_domain": "cpp",
            },
        )


class TestSimpleStubModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyiexample", warningiserror=True)

    def test_integration(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        # Are pyi files preferred
        assert "DoNotFindThis" not in example_file

        foo_sig = example_file.find(id="example.Foo")
        assert foo_sig
        foo = foo_sig.parent
        assert foo.find(id="example.Foo.Meta")
        class_var = foo.find(id="example.Foo.another_class_var")
        class_var_docstring = class_var.parent.find("dd").contents[0].text
        assert class_var_docstring.strip() == "Another class var docstring"
        class_var = foo.find(id="example.Foo.class_var_without_value")
        class_var_docstring = class_var.parent.find("dd").contents[0].text
        assert class_var_docstring.strip() == "A class var without a value."

        method_okay = foo.find(id="example.Foo.method_okay")
        assert method_okay
        method_multiline = foo.find(id="example.Foo.method_multiline")
        assert method_multiline
        method_without_docstring = foo.find(id="example.Foo.method_without_docstring")
        assert method_without_docstring

        # Are constructor arguments from the class docstring parsed?
        init_args = foo.parent.find_next(class_="field-list")
        assert "Set an attribute" in init_args.text


class TestSimpleStubModuleNotPreferred:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyiexample2", warningiserror=True)

    def test_integration(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        # Are py files preferred
        assert "DoNotFindThis" not in example_file

        foo_sig = example_file.find(id="example.Foo")
        assert foo_sig


class TestPy3Module:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py3example")

    def test_integration(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        assert "Initialize self" not in example_file
        assert "a new type" not in example_file

    def test_annotations(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        software = example_file.find(id="example.software")
        assert software
        software_value = software.find(class_="property").contents[-1]
        assert software_value.text.endswith('''"sphin'x"''')
        more_software = example_file.find(id="example.more_software")
        assert more_software
        more_software_value = more_software.find(class_="property").contents[-1]
        assert more_software_value.text.endswith("""'sphinx"autoapi'""")
        interesting = example_file.find(id="example.interesting_string")
        assert interesting
        interesting_value = interesting.find(class_="property").contents[-1]
        assert interesting_value.text.endswith("'interesting\"fun\\'\\\\\\'string'")

        code_snippet = example_file.find(id="example.code_snippet")
        assert code_snippet
        code_snippet_value = code_snippet.find(class_="property").contents[-1]
        assert code_snippet_value.text == "Multiline-String"

        max_rating = example_file.find(id="example.max_rating")
        assert max_rating
        max_rating_value = max_rating.find_all(class_="property")
        assert max_rating_value[0].text == ": int"
        assert max_rating_value[1].text == " = 10"

        # TODO: This should either not have a value
        # or should display the value as part of the type declaration.
        # This prevents setting warningiserror.
        assert example_file.find(id="example.is_valid")

        ratings = example_file.find(id="example.ratings")
        assert ratings
        ratings_value = ratings.find_all(class_="property")
        assert "List[int]" in ratings_value[0].text

        rating_names = example_file.find(id="example.rating_names")
        assert rating_names
        rating_names_value = rating_names.find_all(class_="property")
        assert "Dict[int, str]" in rating_names_value[0].text

        f = example_file.find(id="example.f")
        assert f
        assert f.find(class_="sig-param").text == "start: int"
        assert f.find(class_="sig-return-typehint").text == "Iterable[int]"

        mixed_list = example_file.find(id="example.mixed_list")
        assert mixed_list
        mixed_list_value = mixed_list.find_all(class_="property")
        if sphinx_version >= (6,):
            assert "List[str | int]" in mixed_list_value[0].text
        else:
            assert "List[Union[str, int]]" in mixed_list_value[0].text

        f2 = example_file.find(id="example.f2")
        assert f2
        arg = f2.find(class_="sig-param")
        assert arg.contents[0].text == "not_yet_a"
        assert arg.find("a").text == "A"

        f3 = example_file.find(id="example.f3")
        assert f3
        arg = f3.find(class_="sig-param")
        assert arg.contents[0].text == "imported"
        assert arg.find("a").text == "example2.B"
        returns = f3.find(class_="sig-return-typehint")
        assert returns.find("a").text == "example2.B"

        is_an_a = example_file.find(id="example.A.is_an_a")
        assert is_an_a
        is_an_a_value = is_an_a.find_all(class_="property")
        assert "ClassVar" in is_an_a_value[0].text

        assert example_file.find(id="example.A.instance_var")

        global_a = example_file.find(id="example.global_a")
        assert global_a
        global_a_value = global_a.find_all(class_="property")
        assert global_a_value[0].text == ": A"

        assert example_file.find(id="example.SomeMetaclass")

    def test_overload(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        overloaded_func = example_file.find(id="example.overloaded_func")
        assert overloaded_func
        arg = overloaded_func.find(class_="sig-param")
        assert arg.text == "a: float"
        overloaded_func = overloaded_func.next_sibling.next_sibling
        arg = overloaded_func.find(class_="sig-param")
        assert arg.text == "a: str"
        docstring = overloaded_func.next_sibling.next_sibling
        assert docstring.tag != "dt"
        assert docstring.text.strip() == "Overloaded function"

        overloaded_method = example_file.find(id="example.A.overloaded_method")
        assert overloaded_method
        arg = overloaded_method.find(class_="sig-param")
        assert arg.text == "a: float"
        overloaded_method = overloaded_method.next_sibling.next_sibling
        arg = overloaded_method.find(class_="sig-param")
        assert arg.text == "a: str"
        docstring = overloaded_method.next_sibling.next_sibling
        assert docstring.tag != "dt"
        assert docstring.text.strip() == "Overloaded method"

        overloaded_class_method = example_file.find(
            id="example.A.overloaded_class_method"
        )
        assert overloaded_class_method
        arg = overloaded_class_method.find(class_="sig-param")
        assert arg.text == "a: float"
        overloaded_class_method = overloaded_class_method.next_sibling.next_sibling
        arg = overloaded_class_method.find(class_="sig-param")
        assert arg.text == "a: str"
        docstring = overloaded_class_method.next_sibling.next_sibling
        assert docstring.tag != "dt"
        assert docstring.text.strip() == "Overloaded class method"

        assert example_file.find(id="example.undoc_overloaded_func")
        assert example_file.find(id="example.A.undoc_overloaded_method")

        c = example_file.find(id="example.C")
        assert c
        arg = c.find(class_="sig-param")
        assert arg.text == "a: int"
        c = c.next_sibling.next_sibling
        arg = c.find(class_="sig-param")
        assert arg.text == "a: float"
        docstring = c.next_sibling.next_sibling
        assert docstring.tag != "dt"

        # D inherits overloaded constructor
        d = example_file.find(id="example.D")
        assert d
        arg = d.find(class_="sig-param")
        assert arg.text == "a: int"
        d = d.next_sibling.next_sibling
        arg = d.find(class_="sig-param")
        assert arg.text == "a: float"
        docstring = d.next_sibling.next_sibling
        assert docstring.tag != "dt"

    def test_async(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        async_method = example_file.find(id="example.A.async_method")
        assert async_method.find(class_="property").text.strip() == "async"
        async_function = example_file.find(id="example.async_function")
        assert async_function.find(class_="property").text.strip() == "async"


def test_py3_hiding_undoc_overloaded_members(builder, parse):
    confoverrides = {"autoapi_options": ["members", "special-members"]}
    builder("py3example", confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    overloaded_func = example_file.find(id="example.overloaded_func")
    assert overloaded_func
    overloaded_method = example_file.find(id="example.A.overloaded_method")
    assert overloaded_method
    assert not example_file.find(id="example.undoc_overloaded_func")
    assert not example_file.find(id="example.A.undoc_overloaded_method")


class TestAnnotationCommentsModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyannotationcommentsexample", warningiserror=True)

    def test_integration(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        max_rating = example_file.find(id="example.max_rating")
        assert max_rating
        max_rating_value = max_rating.find_all(class_="property")
        assert max_rating_value[0].text == ": int"
        assert max_rating_value[1].text == " = 10"

        ratings = example_file.find(id="example.ratings")
        assert ratings
        ratings_value = ratings.find_all(class_="property")
        assert "List[int]" in ratings_value[0].text

        rating_names = example_file.find(id="example.rating_names")
        assert rating_names
        rating_names_value = rating_names.find_all(class_="property")
        assert "Dict[int, str]" in rating_names_value[0].text

        f = example_file.find(id="example.f")
        assert f
        assert f.find(class_="sig-param").text == "start: int"
        assert f.find(class_="sig-return-typehint").text == "Iterable[int]"

        mixed_list = example_file.find(id="example.mixed_list")
        assert mixed_list
        mixed_list_value = mixed_list.find_all(class_="property")
        if sphinx_version >= (6,):
            assert "List[str | int]" in mixed_list_value[0].text
        else:
            assert "List[Union[str, int]]" in mixed_list_value[0].text

        f2 = example_file.find(id="example.f2")
        assert f2
        arg = f2.find(class_="sig-param")
        assert arg.contents[0].text == "not_yet_a"
        assert arg.find("a").text == "A"

        is_an_a = example_file.find(id="example.A.is_an_a")
        assert is_an_a
        is_an_a_value = is_an_a.find_all(class_="property")
        assert "ClassVar" in is_an_a_value[0].text

        assert example_file.find(id="example.A.instance_var")

        global_a = example_file.find(id="example.global_a")
        assert global_a
        global_a_value = global_a.find_all(class_="property")
        assert global_a_value[0].text == ": A"


@pytest.mark.skipif(
    sys.version_info < (3, 8), reason="Positional only arguments need Python >=3.8"
)
class TestPositionalOnlyArgumentsModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py38positionalparams", warningiserror=True)

    def test_integration(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        f_simple = example_file.find(id="example.f_simple")
        assert "f_simple(a, b, /, c, d, *, e, f)" in f_simple.text

        if sphinx_version >= (6,):
            f_comment = example_file.find(id="example.f_comment")
            assert (
                "f_comment(a: int, b: int, /, c: int | None, d: int | None, *, e: float, f: float)"
                in f_comment.text
            )
            f_annotation = example_file.find(id="example.f_annotation")
            assert (
                "f_annotation(a: int, b: int, /, c: int | None, d: int | None, *, e: float, f: float)"
                in f_annotation.text
            )
            f_arg_comment = example_file.find(id="example.f_arg_comment")
            assert (
                "f_arg_comment(a: int, b: int, /, c: int | None, d: int | None, *, e: float, f: float)"
                in f_arg_comment.text
            )
        else:
            f_comment = example_file.find(id="example.f_comment")
            assert (
                "f_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
                in f_comment.text
            )
            f_annotation = example_file.find(id="example.f_annotation")
            assert (
                "f_annotation(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
                in f_annotation.text
            )
            f_arg_comment = example_file.find(id="example.f_arg_comment")
            assert (
                "f_arg_comment(a: int, b: int, /, c: Optional[int], d: Optional[int], *, e: float, f: float)"
                in f_arg_comment.text
            )

        f_no_cd = example_file.find(id="example.f_no_cd")
        assert "f_no_cd(a: int, b: int, /, *, e: float, f: float)" in f_no_cd.text


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="Union pipe syntax requires Python >=3.10"
)
class TestPipeUnionModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("py310unionpipe", warningiserror=True)

    def test_integration(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        simple = example_file.find(id="example.simple")
        args = simple.find_all(class_="sig-param")
        assert len(args) == 1
        links = args[0].select("span > a")
        assert len(links) == 1
        assert links[0].text == "pathlib.Path"

        optional = example_file.find(id="example.optional")
        args = optional.find_all(class_="sig-param")
        assert len(args) == 1
        links = args[0].select("span > a")
        assert len(links) == 2
        assert links[0].text == "pathlib.Path"
        assert links[1].text == "None"

        union = example_file.find(id="example.union")
        args = union.find_all(class_="sig-param")
        assert len(args) == 1
        links = args[0].select("span > a")
        assert len(links) == 2
        assert links[0].text == "pathlib.Path"
        assert links[1].text == "None"

        pipe = example_file.find(id="example.pipe")
        args = pipe.find_all(class_="sig-param")
        assert len(args) == 1
        links = args[0].select("span > a")
        assert len(links) == 2
        assert links[0].text == "pathlib.Path"
        assert links[1].text == "None"


def test_napoleon_integration_loaded(builder, parse):
    confoverrides = {
        "exclude_patterns": ["manualapi.rst"],
        "extensions": [
            "autoapi.extension",
            "sphinx.ext.autodoc",
            "sphinx.ext.napoleon",
        ],
    }

    builder("pyexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    method_google = example_file.find(id="example.Foo.method_google_docs")
    params, returns, return_type = method_google.parent.select(".field-list > dt")
    assert params.text == "Parameters:"
    assert returns.text == "Returns:"
    assert return_type.text == "Return type:"


class TestSimplePackage:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pypackageexample", warningiserror=True)

    def test_integration_with_package(self, parse):
        example_file = parse("_build/html/autoapi/package/index.html")

        entries = example_file.find_all(class_="toctree-l1")
        assert any(entry.text == "package.submodule" for entry in entries)
        assert example_file.find(id="package.function")

        example_foo_file = parse("_build/html/autoapi/package/submodule/index.html")

        submodule = example_foo_file.find(id="package.submodule.Class")
        assert submodule
        method_okay = submodule.parent.find(id="package.submodule.Class.method_okay")
        assert method_okay

        index_file = parse("_build/html/index.html")

        toctree = index_file.select("li > a")
        assert any(item.text == "API Reference" for item in toctree)
        assert any(item.text == "package.submodule" for item in toctree)
        assert any(item.text == "Class" for item in toctree)
        assert any(item.text == "function()" for item in toctree)


def test_simple_no_false_warnings(builder, caplog):
    logger = sphinx.util.logging.getLogger("autoapi")
    logger.logger.addHandler(caplog.handler)
    builder("pypackageexample", warningiserror=True)

    assert "Cannot resolve" not in caplog.text


def _test_class_content(builder, parse, class_content):
    confoverrides = {
        "autoapi_python_class_content": class_content,
        "exclude_patterns": ["manualapi.rst"],
    }

    builder("pyexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    foo = example_file.find(id="example.Foo").parent.find("dd")
    if class_content == "init":
        assert "Can we parse arguments" not in foo.text
    else:
        assert "Can we parse arguments" in foo.text

    if class_content not in ("both", "init"):
        assert "Constructor docstring" not in foo.text
    else:
        assert "Constructor docstring" in foo.text


def test_class_class_content(builder, parse):
    _test_class_content(builder, parse, "class")


def test_both_class_content(builder, parse):
    _test_class_content(builder, parse, "both")


def test_init_class_content(builder, parse):
    _test_class_content(builder, parse, "init")


def test_hiding_private_members(builder, parse):
    confoverrides = {"autoapi_options": ["members", "undoc-members", "special-members"]}
    builder("pypackageexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/package/index.html")

    entries = example_file.find_all(class_="toctree-l1")
    assert all("private" not in entry.text for entry in entries)

    assert not pathlib.Path(
        "_build/html/autoapi/package/_private_module/index.html"
    ).exists()


def test_hiding_inheritance(builder, parse):
    confoverrides = {
        "autoapi_options": ["members", "undoc-members", "special-members"],
        "exclude_patterns": ["manualapi.rst"],
    }
    builder("pyexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    assert "Bases:" not in example_file.find(id="example.Foo").parent.find("dd").text


def test_hiding_imported_members(builder, parse):
    confoverrides = {"autoapi_options": ["members", "undoc-members"]}
    builder("pypackagecomplex", confoverrides=confoverrides)

    subpackage_file = parse("_build/html/autoapi/complex/subpackage/index.html")
    assert not subpackage_file.find(id="complex.subpackage.public_chain")

    package_file = parse("_build/html/autoapi/complex/index.html")
    assert not package_file.find(id="complex.public_chain")

    submodule_file = parse("_build/html/autoapi/complex/subpackage/index.html")
    assert not submodule_file.find(id="complex.subpackage.now_public_function")


def test_inherited_members(builder, parse):
    confoverrides = {
        "autoapi_options": ["members", "inherited-members", "undoc-members"],
        "exclude_patterns": ["manualapi.rst"],
    }
    builder("pyexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    bar = example_file.find(id="example.Bar")
    assert bar
    assert bar.parent.find(id="example.Bar.method_okay")


def test_skipping_members(builder, parse):
    builder("pyskipexample", warningiserror=True)

    example_file = parse("_build/html/autoapi/example/index.html")

    assert not example_file.find(id="example.foo")
    assert not example_file.find(id="example.Bar")
    assert not example_file.find(id="example.Bar.m")
    assert example_file.find(id="example.Baf")
    assert not example_file.find(id="example.Baf.m")
    assert not example_file.find(id="example.baz")
    assert example_file.find(id="example.anchor")


@pytest.mark.parametrize(
    "value,order",
    [
        ("bysource", ["Foo", "decorator_okay", "Bar"]),
        ("alphabetical", ["Bar", "Foo", "decorator_okay"]),
        ("groupwise", ["Bar", "Foo", "decorator_okay"]),
    ],
)
def test_order_members(builder, parse, value, order):
    confoverrides = {
        "autoapi_member_order": value,
        "exclude_patterns": ["manualapi.rst"],
    }
    builder("pyexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    indexes = [example_file.find(id=f"example.{name}").sourceline for name in order]
    assert indexes == sorted(indexes)


class _CompareInstanceType:
    def __init__(self, type_):
        self.type = type_

    def __eq__(self, other):
        return self.type is type(other)

    def __repr__(self):
        return "<expect type {}>".format(self.type.__name__)


def test_skip_members_hook(builder):
    os.chdir("tests/python/pyskipexample")
    emit_firstresult_patch = None

    class MockSphinx(Sphinx):
        def __init__(self, *args, **kwargs):
            nonlocal emit_firstresult_patch
            emit_firstresult_patch = Mock(wraps=self.emit_firstresult)
            self.emit_firstresult = emit_firstresult_patch

            super().__init__(*args, **kwargs)

    app = MockSphinx(
        srcdir=".",
        confdir=".",
        outdir="_build/html",
        doctreedir="_build/.doctrees",
        buildername="html",
        warningiserror=True,
        confoverrides={
            "suppress_warnings": [
                "app.add_node",
                "app.add_directive",
                "app.add_role",
            ]
        },
    )
    app.build()

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
        # We don't set warningiserror=True because we test that invalid imports
        # do not fail the build
        builder("pypackagecomplex")

    def test_public_chain_resolves(self, parse):
        submodule_file = parse(
            "_build/html/autoapi/complex/subpackage/submodule/index.html"
        )

        assert submodule_file.find(id="complex.subpackage.submodule.public_chain")

        subpackage_file = parse("_build/html/autoapi/complex/subpackage/index.html")

        assert subpackage_file.find(id="complex.subpackage.public_chain")

        package_file = parse("_build/html/autoapi/complex/index.html")

        assert package_file.find(id="complex.public_chain")

    def test_private_made_public(self, parse):
        submodule_file = parse("_build/html/autoapi/complex/subpackage/index.html")

        assert submodule_file.find(id="complex.subpackage.now_public_function")

    def test_multiple_import_locations(self, parse):
        submodule_file = parse(
            "_build/html/autoapi/complex/subpackage/submodule/index.html"
        )

        assert submodule_file.find(
            id="complex.subpackage.submodule.public_multiple_imports"
        )

        subpackage_file = parse("_build/html/autoapi/complex/subpackage/index.html")

        assert subpackage_file.find(id="complex.subpackage.public_multiple_imports")

        package_file = parse("_build/html/autoapi/complex/index.html")

        assert package_file.find(id="complex.public_multiple_imports")

    def test_simple_wildcard_imports(self, parse):
        wildcard_file = parse("_build/html/autoapi/complex/wildcard/index.html")

        assert wildcard_file.find(id="complex.wildcard.public_chain")
        assert wildcard_file.find(id="complex.wildcard.now_public_function")
        assert wildcard_file.find(id="complex.wildcard.public_multiple_imports")
        assert wildcard_file.find(id="complex.wildcard.module_level_function")

    def test_wildcard_all_imports(self, parse):
        wildcard_file = parse("_build/html/autoapi/complex/wildall/index.html")

        assert not wildcard_file.find(id="complex.wildall.not_all")
        assert not wildcard_file.find(id="complex.wildall.NotAllClass")
        assert not wildcard_file.find(id="complex.wildall.does_not_exist")
        assert wildcard_file.find(id="complex.wildall.SimpleClass")
        assert wildcard_file.find(id="complex.wildall.simple_function")
        assert wildcard_file.find(id="complex.wildall.public_chain")
        assert wildcard_file.find(id="complex.wildall.module_level_function")

    def test_no_imports_in_module_with_all(self, parse):
        foo_file = parse("_build/html/autoapi/complex/foo/index.html")

        assert not foo_file.find(id="complex.foo.module_level_function")

    def test_all_overrides_import_in_module_with_all(self, parse):
        foo_file = parse("_build/html/autoapi/complex/foo/index.html")

        assert foo_file.find(id="complex.foo.PublicClass")

    def test_parses_unicode_file(self, parse):
        foo_file = parse("_build/html/autoapi/complex/unicode_data/index.html")

        assert foo_file.find(id="complex.unicode_data.unicode_str")


class TestComplexPackageParallel(TestComplexPackage):
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pypackagecomplex", parallel=2)


def test_caching(builder, rebuild):
    mtimes = (0, 0)

    def record_mtime():
        nonlocal mtimes
        mtime = 0
        for root, _, files in os.walk("_build/html/autoapi"):
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
        # TODO: Cannot set warningiserror=True because namespaces are not added
        # to the toctree automatically.
        builder("py3implicitnamespace")

    def test_sibling_import_from_namespace(self, parse):
        example_file = parse("_build/html/autoapi/namespace/example/index.html")
        assert example_file.find(id="namespace.example.first_method")

    def test_sub_sibling_import_from_namespace(self, parse):
        example_file = parse("_build/html/autoapi/namespace/example/index.html")
        assert example_file.find(id="namespace.example.second_sub_method")


def test_custom_jinja_filters(builder, parse, tmp_path):
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
                        lambda docstring: "This is using custom filters.\n"
                    )
                }
            )
        ),
        "autoapi_template_dir": str(tmp_path),
        "exclude_patterns": ["manualapi.rst"],
    }
    builder("pyexample", warningiserror=True, confoverrides=confoverrides)

    example_file = parse("_build/html/autoapi/example/index.html")

    foo = example_file.find(id="example.Foo").parent.find("dd")
    assert "This is using custom filters." in foo.text


def test_string_module_attributes(builder):
    """Test toggle for multi-line string attribute values (GitHub #267)."""
    keep_rst = {
        "autoapi_keep_files": True,
    }
    builder("py3example", confoverrides=keep_rst)

    example_path = os.path.join("autoapi", "example", "index.rst")
    with io.open(example_path, encoding="utf8") as example_handle:
        example_file = example_handle.read()

    code_snippet_contents = [
        ".. py:data:: code_snippet",
        "   :value: Multiline-String",
        "",
        "   .. raw:: html",
        "",
        "      <details><summary>Show Value</summary>",
        "",
        "   .. code-block:: python",
        "",
        '      """The following is some code:',
        "      ",  # <--- Line array monstrosity to preserve these leading spaces
        "      # -*- coding: utf-8 -*-",
        "      from __future__ import absolute_import, division, print_function, unicode_literals",
        "      # from future.builtins.disabled import *",
        "      # from builtins import *",
        "      ",
        """      print("chunky o'block")""",
        '      """',
        "",
        "   .. raw:: html",
        "",
        "      </details>",
    ]
    assert "\n".join(code_snippet_contents) in example_file


class TestAutodocTypehintsPackage:
    """Test integrations with the autodoc.typehints extension."""

    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder("pyautodoc_typehints", warningiserror=True)

    def test_renders_typehint(self, parse):
        example_file = parse("_build/html/autoapi/example/index.html")

        test = example_file.find(id="example.A.test")
        args = test.parent.select(".field-list > dd")
        assert args[0].text.startswith("a (int)")

    def test_renders_typehint_in_second_module(self, parse):
        example2_file = parse("_build/html/autoapi/example2/index.html")

        test = example2_file.find(id="example2.B.test")
        args = test.parent.select(".field-list > dd")
        assert args[0].text.startswith("a (int)")


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


class TestMemberOrder:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pyexample",
            warningiserror=True,
            confoverrides={
                "autodoc_member_order": "bysource",
                "autoapi_generate_api_docs": False,
                "autoapi_add_toctree_entry": False,
            },
        )

    def test_line_number_order(self, parse):
        example_file = parse("_build/html/manualapi.html")

        method_tricky = example_file.find(id="example.Foo.method_tricky")
        method_sphinx_docs = example_file.find(id="example.Foo.method_sphinx_docs")

        assert method_tricky.sourceline < method_sphinx_docs.sourceline
