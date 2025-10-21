import io
import os
import shutil
from contextlib import contextmanager

from sphinx.application import Sphinx


@contextmanager
def sphinx_build(test_dir, confoverrides=None):
    os.chdir(f"tests/{test_dir}")
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
    def _run_test(
        self,
        test_dir,
        test_file,
        test_string,
        confoverrides={},
        test_missing: bool = False,
    ):
        with sphinx_build(test_dir, confoverrides=confoverrides):
            with open(test_file, encoding="utf8") as fin:
                text = fin.read().strip()
                if test_missing:
                    assert test_string not in text
                else:
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

    def test_symlink(self):
        """
        Test that the example_function_2 gets added to the TOC Tree when running with symlinks
        and that it does not get added when running without them.
        """
        # Without symlinks, should not contain example_function_2
        self._run_test(
            "toctreeexample",
            "_build/text/index.txt",
            '* "example_function_2()"',
            test_missing=True,
        )

        # With symlinks, should contain example_function_2
        self._run_test(
            "toctreeexample",
            "_build/text/index.txt",
            '* "example_function_2()"',
            confoverrides={"autoapi_follow_symlinks": True},
        )
