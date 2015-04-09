import codecs
try:
    from setuptools import setup, find_packages
    extra_setup = dict(
        install_requires=[
            'PyYAML',
            'epyparse',
            'epydoc',
        ],
    )
except ImportError:
    from distutils.core import setup
    extra_setup = dict(
        requires=[
            'PyYAML',
            'epyparse',
            'epydoc',
        ],
    )

setup(
    name='sphinx-autoapi',
    version='0.1.0',
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
        '': ['_static/*.js', '_static/*.js_t', '_static/*.css'],
    },
    **extra_setup
)
