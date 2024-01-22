import os

import pytest


class TestModule:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pypackageexample",
            warningiserror=True,
            confoverrides={
                "autoapi_own_page_level": "module",
                "autoapi_options": [
                    "members",
                    "undoc-members",
                    "show-inheritance",
                    "imported-members",
                ],
            },
        )

    def test_package(self, parse):
        package_path = "_build/html/autoapi/package/index.html"
        package_file = parse(package_path)

        docstring = package_file.find("p")
        assert docstring.text == "This is a docstring."

        # There should be links to the children with their own page
        subpackages = package_file.find(id="subpackages")
        assert subpackages
        assert subpackages.find("a", string="package.subpackage")
        submodules = package_file.find(id="submodules")
        assert submodules
        assert submodules.find("a", string="package.submodule")

        # There should not be links to the children without their own page
        assert not package_file.find(id="attributes")
        assert not package_file.find(id="exceptions")
        assert not package_file.find(id="classes")
        assert not package_file.find(id="functions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = package_file.find(id="package-contents")
        assert contents.find(id="package.DATA")
        assert contents.find(id="package.MyException")
        assert contents.find(id="package.Class")
        assert contents.find(id="package.Class.class_var")
        assert contents.find(id="package.Class.NestedClass")
        assert contents.find(id="package.Class.method_okay")
        assert contents.find(id="package.Class.NestedClass")
        assert contents.find(id="package.Class.NestedClass.a_classmethod")
        assert contents.find(id="package.function")

    def test_subpackage(self, parse):
        subpackage_path = "_build/html/autoapi/package/subpackage/index.html"
        subpackage_file = parse(subpackage_path)

        docstring = subpackage_file.find("p")
        assert docstring.text == "This is a docstring."

        # There should be links to the children with their own page
        assert not subpackage_file.find(id="subpackages")
        submodules = subpackage_file.find(id="submodules")
        assert submodules
        assert submodules.find("a", string="package.subpackage.submodule")

        # There should not be links to the children without their own page
        assert not subpackage_file.find(id="attributes")
        assert not subpackage_file.find(id="exceptions")
        assert not subpackage_file.find(id="classes")
        assert not subpackage_file.find(id="functions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = subpackage_file.find(id="package-contents")
        assert contents.find(id="package.subpackage.function")

    def test_module(self, parse):
        submodule_path = "_build/html/autoapi/package/submodule/index.html"
        submodule_file = parse(submodule_path)

        docstring = submodule_file.find("p")
        assert docstring.text == "Example module"

        # There should be links to the children with their own page
        pass  # there are no children with their own page

        # There should not be links to the children without their own page
        assert not submodule_file.find(id="submodules")
        assert not submodule_file.find(id="subpackages")
        assert not submodule_file.find(id="attributes")
        assert not submodule_file.find(id="exceptions")
        assert not submodule_file.find(id="classes")
        assert not submodule_file.find(id="functions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = submodule_file.find(id="module-contents")
        assert contents.find(id="package.submodule.DATA")
        assert contents.find(id="package.submodule.MyException")
        assert contents.find(id="package.submodule.Class")
        assert contents.find(id="package.submodule.Class.class_var")
        assert contents.find(id="package.submodule.Class.NestedClass")
        assert contents.find(id="package.submodule.Class.method_okay")
        assert contents.find(id="package.submodule.Class.NestedClass")
        assert contents.find(id="package.submodule.Class.NestedClass.a_classmethod")
        assert contents.find(id="package.submodule.function")

    def test_rendered_only_expected_pages(self):
        _, dirs, files = next(os.walk("_build/html/autoapi/package"))
        assert sorted(dirs) == ["submodule", "subpackage"]
        assert files == ["index.html"]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/submodule"))
        assert not dirs
        assert files == ["index.html"]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/subpackage"))
        assert dirs == ["submodule"]
        assert files == ["index.html"]

        _, dirs, files = next(
            os.walk("_build/html/autoapi/package/subpackage/submodule")
        )
        assert not dirs
        assert files == ["index.html"]

    def test_index(self, parse):
        index_path = "_build/html/autoapi/index.html"
        index_file = parse(index_path)

        top_links = index_file.find_all(class_="toctree-l1")
        top_hrefs = sorted(link.a["href"] for link in top_links)
        assert top_hrefs == [
            "#",
            "package/index.html",
        ]


class TestClass:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pypackageexample",
            warningiserror=True,
            confoverrides={
                "autoapi_own_page_level": "class",
                "autoapi_options": [
                    "members",
                    "undoc-members",
                    "show-inheritance",
                    "imported-members",
                ],
            },
        )

    def test_package(self, parse):
        package_path = "_build/html/autoapi/package/index.html"
        package_file = parse(package_path)

        docstring = package_file.find("p")
        assert docstring.text == "This is a docstring."

        # There should be links to the children with their own page
        subpackages = package_file.find(id="subpackages")
        assert subpackages
        assert subpackages.find("a", string="package.subpackage")
        submodules = package_file.find(id="submodules")
        assert submodules
        assert submodules.find("a", string="package.submodule")
        exceptions = package_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.MyException")
        classes = package_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class")
        assert not classes.find("a", title="package.Class.NestedClass")

        # There should not be links to the children without their own page
        assert not package_file.find(id="attributes")
        assert not package_file.find(id="functions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = package_file.find(id="package-contents")
        assert contents.find(id="package.DATA")
        assert not contents.find(id="package.MyException")
        assert not contents.find(id="package.Class")
        assert not contents.find(id="package.Class.class_var")
        assert not contents.find(id="package.Class.NestedClass")
        assert not contents.find(id="package.Class.method_okay")
        assert not contents.find(id="package.Class.NestedClass")
        assert not contents.find(id="package.Class.NestedClass.a_classmethod")
        assert contents.find(id="package.function")

    def test_module(self, parse):
        submodule_path = "_build/html/autoapi/package/submodule/index.html"
        submodule_file = parse(submodule_path)

        docstring = submodule_file.find("p")
        assert docstring.text == "Example module"

        # There should be links to the children with their own page
        exceptions = submodule_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.submodule.MyException")
        classes = submodule_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.submodule.Class")
        assert not classes.find("a", title="package.submodule.Class.NestedClass")

        # There should not be links to the children without their own page
        assert not submodule_file.find(id="submodules")
        assert not submodule_file.find(id="subpackages")
        assert not submodule_file.find(id="attributes")
        assert not submodule_file.find(id="functions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = submodule_file.find(id="module-contents")
        assert contents.find(id="package.submodule.DATA")
        assert not contents.find(id="package.submodule.MyException")
        assert not contents.find(id="package.submodule.Class")
        assert not contents.find(id="package.submodule.Class.class_var")
        assert not contents.find(id="package.submodule.Class.NestedClass")
        assert not contents.find(id="package.submodule.Class.method_okay")
        assert not contents.find(id="package.submodule.Class.NestedClass")
        assert not contents.find(id="package.submodule.Class.NestedClass.a_classmethod")
        assert contents.find(id="package.submodule.function")

    def test_class(self, parse):
        class_path = "_build/html/autoapi/package/Class.html"
        class_file = parse(class_path)

        class_sig = class_file.find(id="package.Class")
        assert class_sig
        class_ = class_sig.parent
        docstring = class_.find_all("p")[1]
        assert docstring.text == "This is a class."

        # There should be links to the children with their own page
        classes = class_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class.NestedClass")

        # There should not be links to the children without their own page
        assert not class_file.find(id="attributes")
        assert not class_file.find(id="exceptions")
        assert not class_file.find(id="methods")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert class_.find(id="package.Class.class_var")
        assert class_.find(id="package.Class.my_property")
        assert class_.find(id="package.Class.method_okay")

        nested_class_path = "_build/html/autoapi/package/Class.NestedClass.html"
        nested_class_file = parse(nested_class_path)

        nested_class_sig = nested_class_file.find(id="package.Class.NestedClass")
        assert nested_class_sig
        nested_class = nested_class_sig.parent

        # There should be links to the children with their own page
        pass  # there are no children with their own page

        # There should not be links to the children without their own page
        assert not class_file.find(id="attributes")
        assert not class_file.find(id="exceptions")
        assert not class_file.find(id="methods")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert nested_class.find(id="package.Class.NestedClass.a_classmethod")

    def test_exception(self, parse):
        exception_path = "_build/html/autoapi/package/MyException.html"
        exception_file = parse(exception_path)

        exception_sig = exception_file.find(id="package.MyException")
        assert exception_sig
        exception = exception_sig.parent
        docstring = exception.find_all("p")[1]
        assert docstring.text == "This is an exception."

        # There should be links to the children with their own page
        pass  # there are no children with their own page

        # There should not be links to the children without their own page
        assert not exception_file.find(id="attributes")
        assert not exception_file.find(id="exceptions")
        assert not exception_file.find(id="methods")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        pass  # there are no children without their own page

    def test_rendered_only_expected_pages(self):
        _, dirs, files = next(os.walk("_build/html/autoapi/package"))
        assert sorted(dirs) == ["submodule", "subpackage"]
        assert sorted(files) == [
            "Class.NestedClass.html",
            "Class.html",
            "MyException.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/submodule"))
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.html",
            "Class.html",
            "MyException.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/subpackage"))
        assert dirs == ["submodule"]
        assert files == ["index.html"]

        _, dirs, files = next(
            os.walk("_build/html/autoapi/package/subpackage/submodule")
        )
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.html",
            "Class.html",
            "MyException.html",
            "index.html",
        ]

    def test_index(self, parse):
        index_path = "_build/html/autoapi/index.html"
        index_file = parse(index_path)

        top_links = index_file.find_all(class_="toctree-l1")
        top_hrefs = sorted(link.a["href"] for link in top_links)
        assert top_hrefs == [
            "#",
            "package/index.html",
        ]


class TestFunction:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pypackageexample",
            warningiserror=True,
            confoverrides={
                "autoapi_own_page_level": "function",
                "autoapi_options": [
                    "members",
                    "undoc-members",
                    "show-inheritance",
                    "imported-members",
                ],
            },
        )

    def test_package(self, parse):
        package_path = "_build/html/autoapi/package/index.html"
        package_file = parse(package_path)

        docstring = package_file.find("p")
        assert docstring.text == "This is a docstring."

        # There should be links to the children with their own page
        subpackages = package_file.find(id="subpackages")
        assert subpackages
        assert subpackages.find("a", string="package.subpackage")
        submodules = package_file.find(id="submodules")
        assert submodules
        assert submodules.find("a", string="package.submodule")
        classes = package_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class")
        exceptions = package_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.MyException")
        functions = package_file.find(id="functions")
        assert functions
        assert functions.find("a", title="package.function")

        # There should not be links to the children without their own page
        assert not package_file.find(id="attributes")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = package_file.find(id="package-contents")
        assert contents.find(id="package.DATA")
        assert not contents.find(id="package.MyException")
        assert not contents.find(id="package.Class")
        assert not contents.find(id="package.Class.class_var")
        assert not contents.find(id="package.Class.NestedClass")
        assert not contents.find(id="package.Class.method_okay")
        assert not contents.find(id="package.Class.NestedClass")
        assert not contents.find(id="package.Class.NestedClass.a_classmethod")
        assert not contents.find(id="package.function")

    def test_module(self, parse):
        submodule_path = "_build/html/autoapi/package/submodule/index.html"
        submodule_file = parse(submodule_path)

        docstring = submodule_file.find("p")
        assert docstring.text == "Example module"

        # There should be links to the children with their own page
        exceptions = submodule_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.submodule.MyException")
        classes = submodule_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.submodule.Class")
        assert not classes.find("a", title="package.submodule.Class.NestedClass")
        functions = submodule_file.find(id="functions")
        assert functions
        assert functions.find("a", title="package.submodule.function")

        # There should not be links to the children without their own page
        assert not submodule_file.find(id="submodules")
        assert not submodule_file.find(id="subpackages")
        assert not submodule_file.find(id="attributes")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = submodule_file.find(id="module-contents")
        assert contents.find(id="package.submodule.DATA")
        assert not contents.find(id="package.submodule.MyException")
        assert not contents.find(id="package.submodule.Class")
        assert not contents.find(id="package.submodule.Class.class_var")
        assert not contents.find(id="package.submodule.Class.NestedClass")
        assert not contents.find(id="package.submodule.Class.method_okay")
        assert not contents.find(id="package.submodule.Class.NestedClass")
        assert not contents.find(id="package.submodule.Class.NestedClass.a_classmethod")
        assert not contents.find(id="package.submodule.function")

    def test_class(self, parse):
        class_path = "_build/html/autoapi/package/Class.html"
        class_file = parse(class_path)

        class_sig = class_file.find(id="package.Class")
        assert class_sig
        class_ = class_sig.parent
        docstring = class_.find_all("p")[1]
        assert docstring.text == "This is a class."

        # There should be links to the children with their own page
        classes = class_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class.NestedClass")

        # There should not be links to the children without their own page
        assert not class_file.find(id="attributes")
        assert not class_file.find(id="exceptions")
        assert not class_file.find(id="methods")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert class_.find(id="package.Class.class_var")
        assert class_.find(id="package.Class.my_property")
        assert class_.find(id="package.Class.method_okay")

    def test_function(self, parse):
        function_path = "_build/html/autoapi/package/function.html"
        function_file = parse(function_path)

        function_sig = function_file.find(id="package.function")
        assert function_sig

        function_path = "_build/html/autoapi/package/submodule/function.html"
        function_file = parse(function_path)
        assert function_file.find(id="package.submodule.function")

    def test_rendered_only_expected_pages(self):
        _, dirs, files = next(os.walk("_build/html/autoapi/package"))
        assert sorted(dirs) == ["submodule", "subpackage"]
        assert sorted(files) == [
            "Class.NestedClass.html",
            "Class.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/submodule"))
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.html",
            "Class.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/subpackage"))
        assert dirs == ["submodule"]
        assert sorted(files) == ["function.html", "index.html"]

        _, dirs, files = next(
            os.walk("_build/html/autoapi/package/subpackage/submodule")
        )
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.html",
            "Class.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

    def test_index(self, parse):
        index_path = "_build/html/autoapi/index.html"
        index_file = parse(index_path)

        top_links = index_file.find_all(class_="toctree-l1")
        top_hrefs = sorted(link.a["href"] for link in top_links)
        assert top_hrefs == [
            "#",
            "package/index.html",
        ]


class TestMethod:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pypackageexample",
            warningiserror=True,
            confoverrides={
                "autoapi_own_page_level": "method",
                "autoapi_options": [
                    "members",
                    "undoc-members",
                    "show-inheritance",
                    "imported-members",
                ],
            },
        )

    def test_package(self, parse):
        package_path = "_build/html/autoapi/package/index.html"
        package_file = parse(package_path)

        docstring = package_file.find("p")
        assert docstring.text == "This is a docstring."

        # There should be links to the children with their own page
        subpackages = package_file.find(id="subpackages")
        assert subpackages
        assert subpackages.find("a", string="package.subpackage")
        submodules = package_file.find(id="submodules")
        assert submodules
        assert submodules.find("a", string="package.submodule")
        classes = package_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class")
        exceptions = package_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.MyException")
        functions = package_file.find(id="functions")
        assert functions
        assert functions.find("a", title="package.function")

        # There should not be links to the children without their own page
        assert not package_file.find(id="attributes")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = package_file.find(id="package-contents")
        assert contents.find(id="package.DATA")
        assert not contents.find(id="package.MyException")
        assert not contents.find(id="package.Class")
        assert not contents.find(id="package.Class.class_var")
        assert not contents.find(id="package.Class.NestedClass")
        assert not contents.find(id="package.Class.method_okay")
        assert not contents.find(id="package.Class.NestedClass")
        assert not contents.find(id="package.Class.NestedClass.a_classmethod")
        assert not contents.find(id="package.function")

    def test_module(self, parse):
        submodule_path = "_build/html/autoapi/package/submodule/index.html"
        submodule_file = parse(submodule_path)

        docstring = submodule_file.find("p")
        assert docstring.text == "Example module"

        # There should be links to the children with their own page
        exceptions = submodule_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.submodule.MyException")
        classes = submodule_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.submodule.Class")
        assert not classes.find("a", title="package.submodule.Class.NestedClass")
        functions = submodule_file.find(id="functions")
        assert functions
        assert functions.find("a", title="package.submodule.function")

        # There should not be links to the children without their own page
        assert not submodule_file.find(id="submodules")
        assert not submodule_file.find(id="subpackages")
        assert not submodule_file.find(id="attributes")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        contents = submodule_file.find(id="module-contents")
        assert contents.find(id="package.submodule.DATA")
        assert not contents.find(id="package.submodule.MyException")
        assert not contents.find(id="package.submodule.Class")
        assert not contents.find(id="package.submodule.Class.class_var")
        assert not contents.find(id="package.submodule.Class.NestedClass")
        assert not contents.find(id="package.submodule.Class.method_okay")
        assert not contents.find(id="package.submodule.Class.NestedClass")
        assert not contents.find(id="package.submodule.Class.NestedClass.a_classmethod")
        assert not contents.find(id="package.submodule.function")

    def test_class(self, parse):
        class_path = "_build/html/autoapi/package/Class.html"
        class_file = parse(class_path)

        class_sig = class_file.find(id="package.Class")
        assert class_sig
        class_ = class_sig.parent
        docstring = class_.find_all("p")[1]
        assert docstring.text == "This is a class."

        # There should be links to the children with their own page
        classes = class_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class.NestedClass")
        methods = class_file.find(id="methods")
        assert methods
        assert methods.find("a", title="package.Class.method_okay")

        # There should not be links to the children without their own page
        assert not class_file.find(id="attributes")
        assert not class_file.find(id="exceptions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert class_.find(id="package.Class.class_var")
        assert class_.find(id="package.Class.my_property")
        assert not class_.find(id="package.Class.method_okay")

    def test_function(self, parse):
        function_path = "_build/html/autoapi/package/function.html"
        function_file = parse(function_path)

        function_sig = function_file.find(id="package.function")
        assert function_sig

        function_path = "_build/html/autoapi/package/submodule/function.html"
        function_file = parse(function_path)
        assert function_file.find(id="package.submodule.function")

    def test_method(self, parse):
        method_path = "_build/html/autoapi/package/Class.method_okay.html"
        method_file = parse(method_path)

        method_sig = method_file.find(id="package.Class.method_okay")
        assert method_sig

        method_path = "_build/html/autoapi/package/submodule/Class.method_okay.html"
        method_file = parse(method_path)
        assert method_file.find(id="package.submodule.Class.method_okay")

    def test_rendered_only_expected_pages(self):
        _, dirs, files = next(os.walk("_build/html/autoapi/package"))
        assert sorted(dirs) == ["submodule", "subpackage"]
        assert sorted(files) == [
            "Class.NestedClass.a_classmethod.html",
            "Class.NestedClass.html",
            "Class.html",
            "Class.method_okay.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/submodule"))
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.a_classmethod.html",
            "Class.NestedClass.html",
            "Class.html",
            "Class.method_google_docs.html",
            "Class.method_multiline.html",
            "Class.method_okay.html",
            "Class.method_sphinx_docs.html",
            "Class.method_tricky.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/subpackage"))
        assert dirs == ["submodule"]
        assert sorted(files) == ["function.html", "index.html"]

        _, dirs, files = next(
            os.walk("_build/html/autoapi/package/subpackage/submodule")
        )
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.a_classmethod.html",
            "Class.NestedClass.html",
            "Class.html",
            "Class.method_okay.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

    def test_index(self, parse):
        index_path = "_build/html/autoapi/index.html"
        index_file = parse(index_path)

        top_links = index_file.find_all(class_="toctree-l1")
        top_hrefs = sorted(link.a["href"] for link in top_links)
        assert top_hrefs == [
            "#",
            "package/index.html",
        ]


class TestAttribute:
    @pytest.fixture(autouse=True, scope="class")
    def built(self, builder):
        builder(
            "pypackageexample",
            warningiserror=True,
            confoverrides={
                "autoapi_own_page_level": "attribute",
                "autoapi_options": [
                    "members",
                    "undoc-members",
                    "show-inheritance",
                    "imported-members",
                ],
            },
        )

    def test_package(self, parse):
        package_path = "_build/html/autoapi/package/index.html"
        package_file = parse(package_path)

        docstring = package_file.find("p")
        assert docstring.text == "This is a docstring."

        # There should be links to the children with their own page
        subpackages = package_file.find(id="subpackages")
        assert subpackages
        assert subpackages.find("a", string="package.subpackage")
        submodules = package_file.find(id="submodules")
        assert submodules
        assert submodules.find("a", string="package.submodule")
        classes = package_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class")
        exceptions = package_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.MyException")
        functions = package_file.find(id="functions")
        assert functions
        assert functions.find("a", title="package.function")
        attributes = package_file.find(id="attributes")
        assert attributes
        assert attributes.find("a", title="package.DATA")

        # There should not be links to the children without their own page
        pass  # there are no children without their own page

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert not package_file.find(id="package-contents")

    def test_module(self, parse):
        submodule_path = "_build/html/autoapi/package/submodule/index.html"
        submodule_file = parse(submodule_path)

        docstring = submodule_file.find("p")
        assert docstring.text == "Example module"

        # There should be links to the children with their own page
        exceptions = submodule_file.find(id="exceptions")
        assert exceptions
        assert exceptions.find("a", title="package.submodule.MyException")
        classes = submodule_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.submodule.Class")
        assert not classes.find("a", title="package.submodule.Class.NestedClass")
        functions = submodule_file.find(id="functions")
        assert functions
        assert functions.find("a", title="package.submodule.function")
        attributes = submodule_file.find(id="attributes")
        assert attributes
        assert attributes.find("a", title="package.submodule.DATA")

        # There should not be links to the children without their own page
        assert not submodule_file.find(id="submodules")
        assert not submodule_file.find(id="subpackages")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert not submodule_file.find(id="module-contents")

    def test_class(self, parse):
        class_path = "_build/html/autoapi/package/Class.html"
        class_file = parse(class_path)

        class_sig = class_file.find(id="package.Class")
        assert class_sig
        class_ = class_sig.parent
        docstring = class_.find_all("p")[1]
        assert docstring.text == "This is a class."

        # There should be links to the children with their own page
        classes = class_file.find(id="classes")
        assert classes
        assert classes.find("a", title="package.Class.NestedClass")
        methods = class_file.find(id="methods")
        assert methods
        assert methods.find("a", title="package.Class.method_okay")
        attributes = class_file.find(id="attributes")
        assert attributes
        assert attributes.find("a", title="package.Class.class_var")
        assert attributes.find("a", title="package.Class.my_property")

        # There should not be links to the children without their own page
        assert not class_file.find(id="exceptions")

        # Children without their own page should be rendered on this page,
        # and children with their own page should not be rendered on this page.
        assert not class_.find(id="package.Class.class_var")
        assert not class_.find(id="package.Class.my_property")
        assert not class_.find(id="package.Class.method_okay")

    def test_function(self, parse):
        function_path = "_build/html/autoapi/package/function.html"
        function_file = parse(function_path)

        function_sig = function_file.find(id="package.function")
        assert function_sig

        function_path = "_build/html/autoapi/package/submodule/function.html"
        function_file = parse(function_path)
        assert function_file.find(id="package.submodule.function")

    def test_method(self, parse):
        method_path = "_build/html/autoapi/package/Class.method_okay.html"
        method_file = parse(method_path)

        method_sig = method_file.find(id="package.Class.method_okay")
        assert method_sig

        method_path = "_build/html/autoapi/package/submodule/Class.method_okay.html"
        method_file = parse(method_path)
        assert method_file.find(id="package.submodule.Class.method_okay")

    def test_data(self, parse):
        data_path = "_build/html/autoapi/package/DATA.html"
        data_file = parse(data_path)

        data_sig = data_file.find(id="package.DATA")
        assert data_sig

    def test_attribute(self, parse):
        attribute_path = "_build/html/autoapi/package/Class.class_var.html"
        attribute_file = parse(attribute_path)

        attribute_sig = attribute_file.find(id="package.Class.class_var")
        assert attribute_sig

    def test_property(self, parse):
        property_path = "_build/html/autoapi/package/Class.my_property.html"
        property_file = parse(property_path)

        property_sig = property_file.find(id="package.Class.my_property")
        assert property_sig

    def test_rendered_only_expected_pages(self):
        _, dirs, files = next(os.walk("_build/html/autoapi/package"))
        assert sorted(dirs) == ["submodule", "subpackage"]
        assert sorted(files) == [
            "Class.NestedClass.a_classmethod.html",
            "Class.NestedClass.html",
            "Class.class_var.html",
            "Class.html",
            "Class.method_okay.html",
            "Class.my_property.html",
            "DATA.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/submodule"))
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.a_classmethod.html",
            "Class.NestedClass.html",
            "Class.class_var.html",
            "Class.html",
            "Class.method_google_docs.html",
            "Class.method_multiline.html",
            "Class.method_okay.html",
            "Class.method_sphinx_docs.html",
            "Class.method_tricky.html",
            "Class.my_property.html",
            "DATA.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

        _, dirs, files = next(os.walk("_build/html/autoapi/package/subpackage"))
        assert dirs == ["submodule"]
        assert sorted(files) == ["function.html", "index.html"]

        _, dirs, files = next(
            os.walk("_build/html/autoapi/package/subpackage/submodule")
        )
        assert not dirs
        assert sorted(files) == [
            "Class.NestedClass.a_classmethod.html",
            "Class.NestedClass.html",
            "Class.class_var.html",
            "Class.html",
            "Class.method_okay.html",
            "Class.my_property.html",
            "DATA.html",
            "MyException.html",
            "function.html",
            "index.html",
        ]

    def test_index(self, parse):
        index_path = "_build/html/autoapi/index.html"
        index_file = parse(index_path)

        top_links = index_file.find_all(class_="toctree-l1")
        top_hrefs = sorted(link.a["href"] for link in top_links)
        assert top_hrefs == [
            "#",
            "package/index.html",
        ]


@pytest.mark.parametrize(
    "value", ["package", "exception", "property", "data", "not_a_value"]
)
def test_invalid_values(builder, value):
    """Test failure when autoapi_own_page_level is invalid."""
    with pytest.raises(ValueError):
        builder(
            "pypackageexample",
            confoverrides={
                "autoapi_own_page_level": value,
            },
        )
