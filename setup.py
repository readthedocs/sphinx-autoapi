import codecs

from setuptools import setup, find_packages


setup(
    name='sphinx-autoapi',
    version='1.0.0',
    author='Eric Holscher',
    author_email='eric@ericholscher.com',
    url='http://github.com/rtfd/sphinx-autoapi',
    license='BSD',
    description='Sphinx API documentation generator',
    packages=find_packages('.'),
    long_description=codecs.open("README.rst", "r", "utf-8").read(),
    include_package_data=True,
    install_requires=[
        'astroid;python_version>="3"',
        'astroid<2;python_version<"3"',
        'Jinja2',
        'PyYAML',
        'sphinx>=1.6',
        'sphinxcontrib-golangdomain',
        'sphinxcontrib-dotnetdomain',
        'unidecode',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Framework :: Sphinx :: Extension',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
