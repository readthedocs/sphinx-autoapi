import io
import os
import shutil
from contextlib import contextmanager

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
        if os.path.exists("_build"):
            shutil.rmtree("_build")
        os.chdir("../..")


class LanguageIntegrationTests:
    def _run_test(self, test_dir, test_file, test_string):
        with sphinx_build(test_dir):
            with io.open(test_file, encoding="utf8") as fin:
                text = fin.read().strip()
                assert test_string in text


class TestIntegration(LanguageIntegrationTests):
    def test_template_overrides(self):
        self._run_test(
            "templateexample",
            "_build/text/autoapi/example/index.txt",
            "This is a function template override",
        )


class TestTOCTree(LanguageIntegrationTests):
    def test_toctree_overrides(self):
        self._run_test("toctreeexample", "_build/text/index.txt", "API Reference")

    def test_toctree_domain_insertion(self):
        """
        Test that the example_function gets added to the TOC Tree
        """
        self._run_test(
            "toctreeexample", "_build/text/index.txt", '* "example_function()"'
        )
