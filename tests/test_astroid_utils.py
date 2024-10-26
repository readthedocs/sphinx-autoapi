import sys

import astroid
from autoapi import _astroid_utils
from autoapi import _objects
import pytest


def generate_module_names():
    for i in range(1, 5):
        yield ".".join(f"module{j}" for j in range(i))

    yield "package.repeat.repeat"


def imported_basename_cases():
    for module_name in generate_module_names():
        import_ = f"import {module_name}"
        basename = f"{module_name}.ImportedClass"
        expected = basename

        yield (import_, basename, expected)

        import_ = f"import {module_name} as aliased"
        basename = "aliased.ImportedClass"

        yield (import_, basename, expected)

        if "." in module_name:
            from_name, attribute = module_name.rsplit(".", 1)
            import_ = f"from {from_name} import {attribute}"
            basename = f"{attribute}.ImportedClass"
            yield (import_, basename, expected)

            import_ += " as aliased"
            basename = "aliased.ImportedClass"
            yield (import_, basename, expected)

        import_ = f"from {module_name} import ImportedClass"
        basename = "ImportedClass"
        yield (import_, basename, expected)

        import_ = f"from {module_name} import ImportedClass as AliasedClass"
        basename = "AliasedClass"
        yield (import_, basename, expected)


def generate_args():
    for i in range(5):
        yield ", ".join(f"arg{j}" for j in range(i))


def imported_call_cases():
    for args in generate_args():
        for import_, basename, expected in imported_basename_cases():
            basename += f"({args})"
            expected += "()"
            yield import_, basename, expected


class TestAstroidUtils:
    @pytest.mark.parametrize(
        ("import_", "basename", "expected"), list(imported_basename_cases())
    )
    def test_can_get_full_imported_basename(self, import_, basename, expected):
        source = """
        {}
        class ThisClass({}): #@
            pass
        """.format(import_, basename)
        node = astroid.extract_node(source)
        basenames = _astroid_utils.resolve_qualname(node.bases[0], node.basenames[0])
        assert basenames == expected

    @pytest.mark.parametrize(
        ("import_", "basename", "expected"), list(imported_call_cases())
    )
    def test_can_get_full_function_basename(self, import_, basename, expected):
        source = """
        {}
        class ThisClass({}): #@
            pass
        """.format(import_, basename)
        node = astroid.extract_node(source)
        basenames = _astroid_utils.resolve_qualname(node.bases[0], node.basenames[0])
        assert basenames == expected

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ('a = "a"', ("a", "'a'")),
            ("a = 1", ("a", "1")),
            ("a, b, c = (1, 2, 3)", None),
            ("a = b = 1", None),
            ("a = [1, 2, [3, 4]]", ("a", "[1, 2, [3, 4]]")),
            ("a = [1, 2, variable[subscript]]", ("a", None)),
            ('a = """multiline\nstring"""', ("a", '"""multiline\nstring"""')),
            ('a = ["""multiline\nstring"""]', ("a", None)),
            ("a = (1, 2, 3)", ("a", "(1, 2, 3)")),
            ("a = (1, 'two', 3)", ("a", "(1, 'two', 3)")),
            ("a = None", ("a", "None")),
        ],
    )
    def test_can_get_assign_values(self, source, expected):
        node = astroid.extract_node(source)
        value = _astroid_utils.get_assign_value(node)
        assert value == expected

    @pytest.mark.parametrize(
        "signature,expected",
        [
            (
                "a: bool, b: int = 5",
                [(None, "a", "bool", None), (None, "b", "int", "5")],
            ),
            pytest.param(
                "a: bool, /, b: int, *, c: str",
                [
                    (None, "a", "bool", None),
                    ("/", None, None, None),
                    (None, "b", "int", None),
                    ("*", None, None, None),
                    (None, "c", "str", None),
                ],
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            pytest.param(
                "a: bool, /, b: int, *args, c: str, **kwargs",
                [
                    (None, "a", "bool", None),
                    ("/", None, None, None),
                    (None, "b", "int", None),
                    ("*", "args", None, None),
                    (None, "c", "str", None),
                    ("**", "kwargs", None, None),
                ],
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            pytest.param(
                "a: int, *args, b: str, **kwargs",
                [
                    (None, "a", "int", None),
                    ("*", "args", None, None),
                    (None, "b", "str", None),
                    ("**", "kwargs", None, None),
                ],
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
        """.format(signature)
        )

        annotations = _astroid_utils.get_args_info(node.args)
        assert annotations == expected

    def test_parse_split_type_comments(self):
        node = astroid.extract_node(
            """
            def func(
                a, # type: int
                b, # type: int
            ): # type: (...) -> str
                pass
        """
        )

        annotations = _astroid_utils.get_args_info(node.args)

        expected = [
            (None, "a", "int", None),
            (None, "b", "int", None),
        ]
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
            pytest.param(
                "*, a: int, b: int",
                "*, a: int, b: int",
                marks=pytest.mark.skipif(
                    sys.version_info[:2] < (3, 8), reason="Uses Python 3.8+ syntax"
                ),
            ),
            ("a: int, *args, b: str, **kwargs", "a: int, *args, b: str, **kwargs"),
            ("a: 'A'", "a: A"),
            ("a: Literal[1]", "a: Literal[1]"),
            ("a: Literal['x']", "a: Literal['x']"),
            ("a: Literal['x', 'y', 'z']", "a: Literal['x', 'y', 'z']"),
        ],
    )
    def test_format_args(self, signature, expected):
        node = astroid.extract_node(
            """
            def func({}) -> str: #@
                pass
        """.format(signature)
        )

        args_info = _astroid_utils.get_args_info(node.args)
        formatted = _objects._format_args(args_info)
        assert formatted == expected
