import codecs

from setuptools import setup, find_packages


setup(
    name='sphinx-autoapi',
    version='0.6.2',
    author='Eric Holscher',
    author_email='eric@ericholscher.com',
    url='http://github.com/rtfd/sphinx-autoapi',
    license='BSD',
    description='Sphinx auto API documentation generator',
    packages=find_packages('.'),
    long_description=codecs.open("README.rst", "r", "utf-8").read(),
    include_package_data=True,
    install_requires=[
        'astroid;python_version>="3"',
        'astroid<2;python_version<"3"',
        'PyYAML',
        'sphinx',
        'sphinxcontrib-golangdomain',
        'sphinxcontrib-dotnetdomain',
        'unidecode',
    ],
)
