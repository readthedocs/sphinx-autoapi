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
    os.chdir('tests/{0}'.format(test_dir))
    try:
        app = Sphinx(
            srcdir='.',
            confdir='.',
            outdir='_build/text',
            doctreedir='_build/.doctrees',
            buildername='text',
            confoverrides=confoverrides,
        )
        app.build(force_all=True)
        yield
    finally:
        shutil.rmtree('_build')
        os.chdir('../..')


class LanguageIntegrationTests(unittest.TestCase):

    def _run_test(self, test_dir, test_file, test_string):
        with sphinx_build(test_dir):
            with io.open(test_file, encoding='utf8') as fin:
                text = fin.read().strip()
                self.assertIn(test_string, text)


class JavaScriptTests(LanguageIntegrationTests):

    def _js_read(self, path):
        return json.load(open('../fixtures/javascript.json'))

    @patch('autoapi.mappers.javascript.JavaScriptSphinxMapper.read_file', _js_read)
    def test_integration(self):
        self._run_test(
            'jsexample',
            '_build/text/autoapi/Circle/index.txt',
            'Creates an instance of Circle'
        )


class GoTests(LanguageIntegrationTests):

    def _go_read(self, path):
        return json.load(open('../fixtures/go.json'))

    @patch('autoapi.mappers.go.GoSphinxMapper.read_file', _go_read)
    def test_integration(self):
        self._run_test(
            'goexample',
            '_build/text/autoapi/main/index.txt',
            'CopyFuncs produces a json-annotated array of Func objects'
        )


class PythonTests(LanguageIntegrationTests):

    def test_integration(self):
        self.check_integration(
            '_build/text/autoapi/example/index.txt'
        )

    def test_manual_directives(self):
        # The manual directives should contain the same information
        self.check_integration(
            '_build/text/manualapi.txt'
        )

    def check_integration(self, example_path):
        with sphinx_build('pyexample'):
            with io.open(example_path, encoding='utf8') as example_handle:
                example_file = example_handle.read()
            self.assertIn(
                'class example.Foo',
                example_file
            )
            self.assertIn(
                'attr2',
                example_file
            )
            self.assertIn(
                'This is the docstring of an instance attribute.',
                example_file
            )
            self.assertIn(
                'method_okay(self, foo=None, bar=None)',
                example_file
            )
            self.assertIn(
                'method_multiline(self, foo=None, bar=None, baz=None)',
                example_file
            )
            self.assertIn(
                'method_tricky(self, foo=None, bar=dict(foo=1, bar=2))',
                example_file
            )
            # Are constructor arguments from the class docstring parsed?
            self.assertIn(
                'Set an attribute',
                example_file
            )
            # "self" should not be included in constructor arguments
            self.assertNotIn(
                'Foo(self',
                example_file
            )
            self.assertFalse(
                os.path.exists('_build/text/autoapi/method_multiline')
            )
            index_path = '_build/text/index.txt'
            with io.open(index_path, encoding='utf8') as index_handle:
                index_file = index_handle.read()
            self.assertIn(
                'Sphinx AutoAPI Index',
                index_file
            )
            self.assertIn(
                'Foo',
                index_file
            )

    def test_integration_with_package(self):
        with sphinx_build('pypackageexample'):
            example_path = '_build/text/autoapi/example/index.txt'
            with io.open(example_path, encoding='utf8') as example_handle:
                example_file = example_handle.read()
            self.assertIn(
                'example.foo',
                example_file
            )
            self.assertIn(
                'example.module_level_method(foo, bar)',
                example_file
            )

            example_foo_path = '_build/text/autoapi/example/foo/index.txt'
            with io.open(example_foo_path, encoding='utf8') as example_foo_handle:
                example_foo_file = example_foo_handle.read()
            self.assertIn(
                'class example.foo.Foo',
                example_foo_file
            )
            self.assertIn(
                'method_okay(self, foo=None, bar=None)',
                example_foo_file
            )

            index_path = '_build/text/index.txt'
            with io.open(index_path, encoding='utf8') as index_handle:
                index_file = index_handle.read()
            self.assertIn(
                'Sphinx AutoAPI Index',
                index_file
            )
            self.assertIn(
                'example.foo',
                index_file
            )
            self.assertIn(
                'Foo',
                index_file
            )
            self.assertIn(
                'module_level_method',
                index_file
            )

    @pytest.mark.skipif(sphinx.version_info < (1, 4),
                      reason="Cannot override extensions in Sphinx 1.3")
    def test_napoleon_integration(self):
        with sphinx_build('pyexample'):
            example_path = '_build/text/autoapi/example/index.txt'
            with io.open(example_path, encoding='utf8') as example_handle:
                example_file = example_handle.read()

            # Check that docstrings are not transformed without napoleon loaded
            self.assertIn(
                'Args',
                example_file
            )

            self.assertIn(
                'Returns',
                example_file
            )

        confoverrides={
            'extensions': [
                'autoapi.extension',
                'sphinx.ext.autodoc',
                'sphinx.ext.napoleon',
            ],
        }

        with sphinx_build('pyexample', confoverrides=confoverrides):
            example_path = '_build/text/autoapi/example/index.txt'
            with io.open(example_path, encoding='utf8') as example_handle:
                example_file = example_handle.read()

            self.assertIn(
                'Parameters',
                example_file
            )

            self.assertIn(
                'Return type',
                example_file
            )

            self.assertNotIn(
                'Args',
                example_file
            )

    def _test_class_content(self, class_content):
        confoverrides={
            'autoapi_python_class_content': class_content,
        }

        with sphinx_build('pyexample', confoverrides=confoverrides):
            example_path = '_build/text/autoapi/example/index.txt'
            with io.open(example_path, encoding='utf8') as example_handle:
                example_file = example_handle.read()

                assert_class = self.assertIn
                if class_content == 'init':
                    assert_class = self.assertNotIn

                assert_class(
                    'Can we parse arguments',
                    example_file
                )

                assert_init = self.assertIn
                if class_content not in ('both', 'init'):
                    assert_init = self.assertNotIn

                assert_init(
                    'Constructor docstring',
                    example_file
                )

    def test_class_class_content(self):
        self._test_class_content('class')

    def test_both_class_content(self):
        self._test_class_content('both')

    def test_init_class_content(self):
        self._test_class_content('init')


class DotNetTests(LanguageIntegrationTests):

    def _dotnet_read(self, path):
        return json.load(open('../fixtures/dotnet.json'))

    # Mock this because it's slow otherwise
    def _dotnet_load(self, patterns, dirs, ignore=[]):
        data = self.read_file(path='inmem')
        self.paths['inmem'] = data

    @staticmethod
    def _dotnet_finished(app, exception):
        pass

    @patch('autoapi.mappers.dotnet.DotNetSphinxMapper.load', _dotnet_load)
    @patch('autoapi.mappers.dotnet.DotNetSphinxMapper.read_file', _dotnet_read)
    @patch('autoapi.mappers.dotnet.DotNetSphinxMapper.build_finished', _dotnet_finished)
    def test_integration(self):
        self._run_test(
            'dotnetexample',
            '_build/text/autoapi/Microsoft/AspNet/Identity/IUserStore-TUser/index.txt',
            'Provides an abstraction for a store which manages user accounts.'
        )


class IntegrationTests(LanguageIntegrationTests):

    def test_template_overrides(self):
        self._run_test(
            'templateexample',
            '_build/text/autoapi/example/index.txt',
            'This is a fuction template override'
        )


class TOCTreeTests(LanguageIntegrationTests):

    def test_toctree_overrides(self):
        self._run_test(
            'toctreeexample',
            '_build/text/index.txt',
            'AutoAPI Index'
        )

    def test_toctree_domain_insertion(self):
        """
        Test that the example_function gets added to the TOC Tree
        """
        self._run_test(
            'toctreeexample',
            '_build/text/index.txt',
            '* example_function'
        )
