import sys

import astroid
from autoapi.mappers.python import astroid_utils
import pytest


def generate_module_names():
    for i in range(1, 5):
        yield ".".join("module{}".format(j) for j in range(i))

    yield "package.repeat.repeat"


def imported_basename_cases():
    for module_name in generate_module_names():
        import_ = "import {}".format(module_name)
        basename = "{}.ImportedClass".format(module_name)
        expected = basename

        yield (import_, basename, expected)

        import_ = "import {} as aliased".format(module_name)
        basename = "aliased.ImportedClass"

        yield (import_, basename, expected)

        if "." in module_name:
            from_name, attribute = module_name.rsplit(".", 1)
            import_ = "from {} import {}".format(from_name, attribute)
            basename = "{}.ImportedClass".format(attribute)
            yield (import_, basename, expected)

            import_ += " as aliased"
            basename = "aliased.ImportedClass"
            yield (import_, basename, expected)

        import_ = "from {} import ImportedClass".format(module_name)
        basename = "ImportedClass"
        yield (import_, basename, expected)

        import_ = "from {} import ImportedClass as AliasedClass".format(module_name)
        basename = "AliasedClass"
        yield (import_, basename, expected)


def generate_args():
    for i in range(5):
        yield ", ".join("arg{}".format(j) for j in range(i))


def imported_call_cases():
    for args in generate_args():
        for import_, basename, expected in imported_basename_cases():
            basename += "({})".format(args)
            expected += "()"
            yield import_, basename, expected


class TestAstroidUtils(object):
    @pytest.mark.parametrize(
        ("import_", "basename", "expected"), list(imported_basename_cases())
    )
    def test_can_get_full_imported_basename(self, import_, basename, expected):
        source = """
        {}
        class ThisClass({}): #@
            pass
        """.format(
            import_, basename
        )
        node = astroid.extract_node(source)
        basenames = astroid_utils.get_full_basename(node.bases[0], node.basenames[0])
        assert basenames == expected

    @pytest.mark.parametrize(
        ("import_", "basename", "expected"), list(imported_call_cases())
    )
    def test_can_get_full_function_basename(self, import_, basename, expected):
        source = """
        {}
        class ThisClass({}): #@
            pass
        """.format(
            import_, basename
        )
        node = astroid.extract_node(source)
        basenames = astroid_utils.get_full_basename(node.bases[0], node.basenames[0])
        assert basenames == expected

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ('a = "a"', ("a", "a")),
            ("a = 1", ("a", 1)),
            ("a, b, c = (1, 2, 3)", None),
            ("a = b = 1", None),
        ],
    )
    def test_can_get_assign_values(self, source, expected):
        node = astroid.extract_node(source)
        value = astroid_utils.get_assign_value(node)
        assert value == expected

    @pytest.mark.parametrize(
        "signature,expected",
        [
            ("a: bool, b: int = 5", {"a": "bool", "b": "int"}),
            pytest.param(
                "a: bool, /, b: int, *, c: str",
                {"a": "bool", "b": "int", "c": "str"},
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            pytest.param(
                "a: bool, /, b: int, *args, c: str, **kwargs",
                {"a": "bool", "b": "int", "c": "str"},
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            pytest.param(
                "a: int, *args, b: str, **kwargs",
                {"a": "int", "b": "str"},
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
        ],
    )
    def test_parse_annotations(self, signature, expected):
        node = astroid.extract_node(
            """
            def func({}) -> str: #@
                pass
        """.format(
                signature
            )
        )

        annotations = astroid_utils.get_annotations_dict(node.args)
        assert annotations == expected

    @pytest.mark.parametrize(
        "signature,expected",
        [
            ("a: bool, b: int = 5, c='hi'", "a: bool, b: int = 5, c='hi'"),
            pytest.param(
                "a: bool, /, b: int, *, c: str",
                "a: bool, /, b: int, *, c: str",
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            pytest.param(
                "a: bool, /, b: int, *args, c: str, **kwargs",
                "a: bool, /, b: int, *args, c: str, **kwargs",
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            ("a: int, *args, b: str, **kwargs", "a: int, *args, b: str, **kwargs"),
            ("a: 'A'", "a: A"),
        ],
    )
    def test_format_args(self, signature, expected):
        node = astroid.extract_node(
            """
            def func({}) -> str: #@
                pass
        """.format(
                signature
            )
        )

        formatted = astroid_utils.format_args(node.args)
        assert formatted == expected
