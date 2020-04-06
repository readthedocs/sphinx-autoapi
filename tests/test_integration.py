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
from sphinx.errors import ExtensionError


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
        if os.path.exists("_build"):
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


@pytest.mark.skipif(
    sphinx.version_info >= (3,),
    reason="golangdomain extension does not support sphinx >=3",
)
class GoTests(LanguageIntegrationTests):
    def _go_read(self, path, **kwargs):
        return json.load(open("../fixtures/go.json"))

    @patch("autoapi.mappers.go.GoSphinxMapper.read_file", _go_read)
    def test_integration(self):
        self._run_test(
            "goexample",
            "_build/text/autoapi/main/index.txt",
            "CopyFuncs produces a json-annotated array of Func objects",
        )


@pytest.mark.skipif(
    sphinx.version_info >= (3,),
    reason="dotnetdomain extension does not support sphinx >=3",
)
class DotNetTests(LanguageIntegrationTests):
    def _dotnet_read(self, path):
        return json.load(open("../fixtures/dotnet.json"))

    # Mock this because it's slow otherwise
    def _dotnet_load(self, patterns, dirs, ignore=()):
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
        self._run_test("toctreeexample", "_build/text/index.txt", "API Reference")

    def test_toctree_domain_insertion(self):
        """
        Test that the example_function gets added to the TOC Tree
        """
        self._run_test("toctreeexample", "_build/text/index.txt", "* example_function")


class TestExtensionErrors:
    @pytest.fixture(autouse=True)
    def unload_go_and_dotned_libraries(self):
        # unload dotnet and golang domain libraries, because they may be imported before
        for mod_name in ("sphinxcontrib.dotnetdomain", "sphinxcontrib.golangdomain"):
            try:
                del sys.modules[mod_name]
            except KeyError:
                pass

    @pytest.mark.parametrize(
        "proj_name, override_conf, err_msg",
        [
            (
                "toctreeexample",
                {"autoapi_type": "INVALID VALUE"},
                (
                    "Invalid autoapi_type setting, following values is "
                    'allowed: "dotnet", "go", "javascript", "python"'
                ),
            ),
            (
                "goexample",
                {"autoapi_type": "go", "extensions": ["autoapi.extension"]},
                (
                    "AutoAPI of type `go` requires following "
                    "packages to be installed and included in extensions list: "
                    "sphinxcontrib.golangdomain (available as "
                    '"sphinxcontrib-golangdomain" on PyPI)'
                ),
            ),
            (
                "dotnetexample",
                {"autoapi_type": "dotnet", "extensions": ["autoapi.extension"]},
                (
                    "AutoAPI of type `dotnet` requires following "
                    "packages to be installed and included in extensions list: "
                    "sphinxcontrib.dotnetdomain (available as "
                    '"sphinxcontrib-dotnetdomain" on PyPI)'
                ),
            ),
        ],
    )
    def test_extension_setup_errors(self, proj_name, override_conf, err_msg):
        with pytest.raises(ExtensionError) as err_info:
            with sphinx_build(proj_name, override_conf):
                pass

        assert str(err_info.value) == err_msg
