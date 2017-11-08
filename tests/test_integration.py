import io
import json
import os
import sys
import shutil
import unittest
from contextlib import contextmanager

from mock import patch

from sphinx.application import Sphinx


@contextmanager
def sphinx_build(test_dir):
    os.chdir('tests/{0}'.format(test_dir))
    try:
        app = Sphinx(
            srcdir='.',
            confdir='.',
            outdir='_build/text',
            doctreedir='_build/.doctrees',
            buildername='text',
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
        with sphinx_build('pyexample'):
            example_path = '_build/text/autoapi/example/index.txt'
            with io.open(example_path, encoding='utf8') as example_handle:
                example_file = example_handle.read()
            self.assertIn(
                'class example.Foo',
                example_file
            )
            self.assertIn(
                'method_okay(foo=None, bar=None)',
                example_file
            )
            self.assertIn(
                'method_multiline(foo=None, bar=None, baz=None)',
                example_file
            )
            self.assertIn(
                'method_tricky(foo=None, bar=dict)',
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
