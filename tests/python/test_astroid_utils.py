import astroid
from autoapi.mappers.python import astroid_utils
import pytest


@pytest.mark.parametrize(
    "signature,expected",
    [
        ("a: bool, b: int = 5", {"a": "bool", "b": "int"}),
        ("a: bool, /, b: int, *, c: str", {"a": "bool", "b": "int", "c": "str"}),
        (
            "a: bool, /, b: int, *args, c: str, **kwargs",
            {"a": "bool", "b": "int", "c": "str"},
        ),
        ("a: int, *args, b: str, **kwargs", {"a": "int", "b": "str"}),
    ],
)
def test_parse_annotations(signature, expected):
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
        ("a: bool, /, b: int, *, c: str", "a: bool, /, b: int, *, c: str"),
        (
            "a: bool, /, b: int, *args, c: str, **kwargs",
            "a: bool, /, b: int, *args, c: str, **kwargs",
        ),
        ("a: int, *args, b: str, **kwargs", "a: int, *args, b: str, **kwargs"),
        ("a: 'A'", "a: A"),
    ],
)
def test_format_args(signature, expected):
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
