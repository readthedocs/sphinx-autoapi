import io

from setuptools import setup, find_packages

version = {}
with open("autoapi/_version.py") as fp:
    exec(fp.read(), version)

setup(
    name="sphinx-autoapi",
    version=version["__version__"],
    author="Eric Holscher",
    author_email="eric@ericholscher.com",
    url="http://github.com/readthedocs/sphinx-autoapi",
    license="BSD",
    description="Sphinx API documentation generator",
    packages=find_packages("."),
    long_description=io.open("README.rst", "r", encoding="utf-8").read(),
    include_package_data=True,
    install_requires=[
        "astroid>=2.4",
        "Jinja2",
        "PyYAML",
        "sphinx>=3.0",
        "unidecode",
    ],
    extras_require={
        "docs": ["sphinx", "sphinx_rtd_theme"],
        "go": ["sphinxcontrib-golangdomain"],
        "dotnet": ["sphinxcontrib-dotnetdomain"],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Framework :: Sphinx :: Extension",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
