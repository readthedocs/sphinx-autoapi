import io
import json
import os
import sys
import shutil
import unittest
from contextlib import contextmanager

from mock import patch
import pytest

import sphinx
from sphinx.application import Sphinx


@contextmanager
def sphinx_build(test_dir, confoverrides=None):
    os.chdir("tests/{0}".format(test_dir))
    try:
        app = Sphinx(
            srcdir=".",
            confdir=".",
            outdir="_build/text",
            doctreedir="_build/.doctrees",
            buildername="text",
            confoverrides=confoverrides,
        )
        app.build(force_all=True)
        yield
    finally:
        shutil.rmtree("_build")
        os.chdir("../..")


class LanguageIntegrationTests(unittest.TestCase):
    def _run_test(self, test_dir, test_file, test_string):
        with sphinx_build(test_dir):
            with io.open(test_file, encoding="utf8") as fin:
                text = fin.read().strip()
                self.assertIn(test_string, text)


class JavaScriptTests(LanguageIntegrationTests):
    def _js_read(self, path):
        return json.load(open("../fixtures/javascript.json"))

    @patch("autoapi.mappers.javascript.JavaScriptSphinxMapper.read_file", _js_read)
    def test_integration(self):
        self._run_test(
            "jsexample",
            "_build/text/autoapi/Circle/index.txt",
            "Creates an instance of Circle",
        )


class GoTests(LanguageIntegrationTests):
    def _go_read(self, path):
        return json.load(open("../fixtures/go.json"))

    @patch("autoapi.mappers.go.GoSphinxMapper.read_file", _go_read)
    def test_integration(self):
        self._run_test(
            "goexample",
            "_build/text/autoapi/main/index.txt",
            "CopyFuncs produces a json-annotated array of Func objects",
        )


class DotNetTests(LanguageIntegrationTests):
    def _dotnet_read(self, path):
        return json.load(open("../fixtures/dotnet.json"))

    # Mock this because it's slow otherwise
    def _dotnet_load(self, patterns, dirs, ignore=[]):
        data = self.read_file(path="inmem")
        self.paths["inmem"] = data

    @staticmethod
    def _dotnet_finished(app, exception):
        pass

    @patch("autoapi.mappers.dotnet.DotNetSphinxMapper.load", _dotnet_load)
    @patch("autoapi.mappers.dotnet.DotNetSphinxMapper.read_file", _dotnet_read)
    @patch("autoapi.mappers.dotnet.DotNetSphinxMapper.build_finished", _dotnet_finished)
    def test_integration(self):
        self._run_test(
            "dotnetexample",
            "_build/text/autoapi/Microsoft/AspNet/Identity/IUserStore-TUser/index.txt",
            "Provides an abstraction for a store which manages user accounts.",
        )


class IntegrationTests(LanguageIntegrationTests):
    def test_template_overrides(self):
        self._run_test(
            "templateexample",
            "_build/text/autoapi/example/index.txt",
            "This is a fuction template override",
        )


class TOCTreeTests(LanguageIntegrationTests):
    def test_toctree_overrides(self):
        self._run_test("toctreeexample", "_build/text/index.txt", "AutoAPI Index")

    def test_toctree_domain_insertion(self):
        """
        Test that the example_function gets added to the TOC Tree
        """
        self._run_test("toctreeexample", "_build/text/index.txt", "* example_function")
