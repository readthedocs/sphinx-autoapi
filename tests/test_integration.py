import json
import os
import sys
import shutil
import unittest

from mock import patch

from sphinx.application import Sphinx


class LanguageIntegrationTests(unittest.TestCase):

    def _run_test(self, test_dir, test_file, test_string):
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
            with open(test_file) as fin:
                text = fin.read().strip()
                self.assertIn(test_string, text)
        finally:
            shutil.rmtree('_build')
            os.chdir('../..')


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

    @unittest.skipIf(sys.version_info > (3, 0), 'Epydoc does not support Python 3')
    def test_integration(self):
        self._run_test(
            'pyexample',
            '_build/text/autoapi/example/index.txt',
            'Compute the square root of x and return it'
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
            '_build/text/autoapi/Microsoft/AspNet/JsonPatch/Adapters/IObjectAdapter-TModel/index.txt',
            'Defines the operations that can be performed on a JSON patch document.'
        )


class IntegrationTests(LanguageIntegrationTests):

    @unittest.skipIf(sys.version_info > (3, 0), 'Epydoc does not support Python 3')
    def test_template_overrides(self):
        self._run_test(
            'templateexample',
            '_build/text/autoapi/example/index.txt',
            'This is a fuction template override'
        )


class TOCTreeTests(LanguageIntegrationTests):

    @unittest.skipIf(sys.version_info > (3, 0), 'Epydoc does not support Python 3')
    def test_toctree_overrides(self):
        self._run_test(
            'toctreeexample',
            '_build/text/index.txt',
            'AutoAPI Index'
        )
