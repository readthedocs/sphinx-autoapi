from .mappers import (
    DotNetSphinxMapper,
    PythonSphinxMapper,
    GoSphinxMapper,
    JavaScriptSphinxMapper,
)

default_file_mapping = {
    "python": ["*.py", "*.pyi"],
    "dotnet": ["project.json", "*.csproj", "*.vbproj"],
    "go": ["*.go"],
    "javascript": ["*.js"],
}


default_ignore_patterns = {
    "dotnet": ["*toc.yml", "*index.yml"],
    "python": ["*migrations*"],
}


default_backend_mapping = {
    "python": PythonSphinxMapper,
    "dotnet": DotNetSphinxMapper,
    "go": GoSphinxMapper,
    "javascript": JavaScriptSphinxMapper,
}


#: describes backend requirements in form
#: {'backend name': (('1st package name in pypi', '1st package import name'), ...)}
backend_requirements = {
    "python": (),
    "javascript": (),
    "go": (("sphinxcontrib-golangdomain", "sphinxcontrib.golangdomain"),),
    "dotnet": (("sphinxcontrib-dotnetdomain", "sphinxcontrib.dotnetdomain"),),
}  # type: (Dict[str, Sequence[Tuple[str, str]]])


def _get_available_backends():
    def is_importable(name):
        try:
            __import__(name)
            return True
        except ModuleNotFoundError:
            return False

    backends = set()
    for backend_name, deps in backend_requirements.items():
        if all(is_importable(import_name) for _, import_name in deps):
            backends.add(backend_name)

    return backends


available_backends = _get_available_backends()


del _get_available_backends
