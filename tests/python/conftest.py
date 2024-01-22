import io
import os
import pathlib
import shutil
from unittest.mock import call

from bs4 import BeautifulSoup
import pytest
from sphinx.application import Sphinx


@pytest.fixture(scope="session")
def rebuild():
    def _rebuild(confdir=".", **kwargs):
        app = Sphinx(
            srcdir=".",
            confdir=confdir,
            outdir="_build/html",
            doctreedir="_build/.doctrees",
            buildername="html",
            pdb=True,
            **kwargs,
        )
        app.build()

    return _rebuild


@pytest.fixture(scope="class")
def builder(rebuild):
    cwd = os.getcwd()

    def build(test_dir, **kwargs):
        if kwargs.get("warningiserror"):
            # Add any warnings raised when using `Sphinx` more than once
            # in a Python session.
            confoverrides = kwargs.setdefault("confoverrides", {})
            confoverrides.setdefault("suppress_warnings", [])
            suppress = confoverrides["suppress_warnings"]
            suppress.append("app.add_node")
            suppress.append("app.add_directive")
            suppress.append("app.add_role")

        os.chdir("tests/python/{0}".format(test_dir))
        rebuild(**kwargs)

    yield build

    try:
        shutil.rmtree("_build")
        if (pathlib.Path("autoapi") / "index.rst").exists():
            shutil.rmtree("autoapi")
    finally:
        os.chdir(cwd)


@pytest.fixture(scope="class")
def parse():
    cache = {}

    def parser(path):
        if path not in cache:
            with io.open(path, encoding="utf8") as file_handle:
                cache[path] = BeautifulSoup(file_handle, features="html.parser")

        return cache[path]

    yield parser
