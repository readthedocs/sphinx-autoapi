import codecs
try:
    from setuptools import setup, find_packages
    extra_setup = dict(
        install_requires=[
            'PyYAML',
            'epyparse',
            'epydoc',
            'sphinx',
            'sphinxcontrib-golangdomain',
            'sphinxcontrib-dotnetdomain',
            'unidecode',
        ],
        test_suite='nose.collector',
        tests_require=['nose', 'mock'],
    )
except ImportError:
    from distutils.core import setup
    extra_setup = dict(
        requires=[
            'PyYAML',
            'epyparse',
            'epydoc',
            'sphinx'
            'sphinxcontrib-golangdomain',
            'sphinxcontrib-dotnetdomain',
            'unidecode',
        ],
    )

setup(
    name='sphinx-autoapi',
    version='0.4.0',
    author='Eric Holscher',
    author_email='eric@ericholscher.com',
    url='http://github.com/ericholscher/sphinx-autoapi',
    license='BSD',
    description='',
    package_dir={'': '.'},
    packages=find_packages('.'),
    long_description=codecs.open("README.rst", "r", "utf-8").read(),
    # trying to add files...
    include_package_data=True,
    package_data={
        'autoapi': [
            'templates/*.rst',
            'templates/*/*.rst',
        ],
    },
    **extra_setup
)
