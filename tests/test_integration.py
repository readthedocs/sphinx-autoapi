import os
import shutil
import subprocess as sp
import unittest

__author__ = 'swenson'


class LanguageIntegrationTests(unittest.TestCase):

    def test_full_py(self):
        os.chdir('tests/pyexample')
        try:
            if os.path.exists('_build'):
                shutil.rmtree('_build')
            os.mkdir('_build')
            sp.check_call('sphinx-build -b text -d _build/doctrees . _build/text', shell=True)

            with open('_build/text/autoapi/example/index.txt') as fin:
                text = fin.read().strip()
            self.assertIn('Compute the square root of x and return it.', text)
        finally:
            os.chdir('../..')

    def test_full_js(self):
        os.chdir('tests/jsexample')
        try:
            if os.path.exists('_build'):
                shutil.rmtree('_build')
            os.mkdir('_build')
            sp.check_call('sphinx-build -b text -d _build/doctrees . _build/text', shell=True)

            with open('_build/text/autoapi/Circle/index.txt') as fin:
                text = fin.read().strip()
                self.assertIn('Creates an instance of Circle', text)
        finally:
            os.chdir('../..')

    def test_full_go(self):
        os.chdir('tests/goexample')
        try:
            if os.path.exists('_build'):
                shutil.rmtree('_build')
            os.mkdir('_build')
            sp.check_call('sphinx-build -b text -d _build/doctrees . _build/text', shell=True)

            with open('_build/text/autoapi/main/index.txt') as fin:
                text = fin.read().strip()
                self.assertIn(
                    'CopyFuncs produces a json-annotated array of Func objects',
                    text
                )
        finally:
            os.chdir('../..')

    def test_full_dotnet(self):
        os.chdir('tests/dotnetexample')
        try:
            if os.path.exists('_build'):
                shutil.rmtree('_build')
            os.mkdir('_build')
            sp.check_call('sphinx-build -b text -d _build/doctrees . _build/text', shell=True)

            with open('_build/text/autoapi/Microsoft/CodeAnalysis/AdhocWorkspace/index.txt') as fin:
                text = fin.read().strip()
                self.assertIn(
                    'A workspace that allows full manipulation of projects and documents',
                    text
                )
        finally:
            os.chdir('../..')


class FeatureIntegrationTests(unittest.TestCase):

    def test_template_override(self):
        """
        Test that we are overriding the template properly.

        This uses the ``template_overrides/python/function.rst`` template to override content.
        """
        os.chdir('tests/templateexample')
        try:
            if os.path.exists('_build'):
                shutil.rmtree('_build')
            os.mkdir('_build')
            sp.check_call('sphinx-build -b text -d _build/doctrees . _build/text', shell=True)

            with open('_build/text/autoapi/example/index.txt') as fin:
                text = fin.read().strip()
                self.assertIn('This is a fuction template override!', text)
        finally:
            os.chdir('../..')
