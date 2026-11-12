import astroid
import pytest
from sphinx.ext.inheritance_diagram import InheritanceException

from autoapi.inheritance_diagrams import _import_class


@pytest.fixture
def namedtuple_module(tmp_path, monkeypatch):
    (tmp_path / "nt_module.py").write_text(
        "from collections import namedtuple\n"
        "\n"
        'Point = namedtuple("Point", ["x", "y"])\n'
        "\n"
        "class Base:\n"
        '    Pair = namedtuple("Pair", ["a", "b"])\n'
        "\n"
        "value = 1\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    yield "nt_module"
    astroid.MANAGER.astroid_cache.pop("nt_module", None)


@pytest.mark.parametrize("name", ["Point", "Base.Pair"])
def test_import_namedtuple(namedtuple_module, name):
    classes = _import_class(f"{namedtuple_module}.{name}", None)

    assert [cls.name for cls in classes] == [name.rsplit(".", 1)[-1]]
    assert "tuple" in [base.name for base in classes[0].ancestors()]


def test_import_non_class_assignment(namedtuple_module):
    with pytest.raises(InheritanceException, match="is not a class or module"):
        _import_class(f"{namedtuple_module}.value", None)
