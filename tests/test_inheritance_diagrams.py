from autoapi.inheritance_diagrams import _import_class
import pytest
from sphinx.ext.inheritance_diagram import InheritanceException


@pytest.fixture
def shadowing_package(tmp_path, monkeypatch):
    """A package where an absolute import shadows a submodule with an instance."""
    package = tmp_path / "shadowing_pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        "from shadowing_pkg.shadowed import shadowed\n"
    )
    (package / "shadowed.py").write_text(
        "class Base:\n"
        "    pass\n"
        "\n"
        "class Child(Base):\n"
        "    attribute = Base()\n"
        "\n"
        "shadowed = Base()\n"
    )
    monkeypatch.syspath_prepend(tmp_path)


@pytest.mark.usefixtures("shadowing_package")
def test_import_class_through_name_that_shadows_a_submodule():
    classes = _import_class("shadowing_pkg.shadowed.Child", None)

    assert [cls.qname() for cls in classes] == ["shadowing_pkg.shadowed.Child"]


@pytest.mark.usefixtures("shadowing_package")
def test_import_class_through_instance_attribute_of_a_class():
    with pytest.raises(InheritanceException, match="Could not import"):
        _import_class("shadowing_pkg.shadowed.Child.attribute.Missing", None)
