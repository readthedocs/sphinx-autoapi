import os
import shutil
import subprocess as sp
import unittest

from sphinx.application import Sphinx


class LanguageIntegrationTests(unittest.TestCase):

    tests = (
        (
            'pyexample',
            '_build/text/autoapi/example/index.txt',
            'Compute the square root of x and return it'
        ),
        (
            'jsexample',
            '_build/text/autoapi/Circle/index.txt',
            'Creates an instance of Circle'
        ),
        (
            'goexample',
            '_build/text/autoapi/main/index.txt',
            'CopyFuncs produces a json-annotated array of Func objects'
        ),
        (
            'dotnetexample',
            '_build/text/autoapi/Microsoft/CodeAnalysis/AdhocWorkspace/index.txt',
            'A workspace that allows full manipulation of projects and documents'
        ),
        (
            'templateexample',
            '_build/text/autoapi/example/index.txt',
            'This is a fuction template override'
        ),
    )

    def test_basic_integration(self):
        for test_dir, test_file, test_string in self.tests:
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

