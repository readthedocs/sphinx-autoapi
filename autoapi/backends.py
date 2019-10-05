from .mappers import (
    DotNetSphinxMapper,
    PythonSphinxMapper,
    GoSphinxMapper,
    JavaScriptSphinxMapper,
)

DEFAULT_FILE_PATTERNS = {
    "python": ["*.py", "*.pyi"],
    "dotnet": ["project.json", "*.csproj", "*.vbproj"],
    "go": ["*.go"],
    "javascript": ["*.js"],
}


DEFAULT_IGNORE_PATTERNS = {
    "dotnet": ["*toc.yml", "*index.yml"],
    "python": ["*migrations*"],
}


LANGUAGE_MAPPERS = {
    "python": PythonSphinxMapper,
    "dotnet": DotNetSphinxMapper,
    "go": GoSphinxMapper,
    "javascript": JavaScriptSphinxMapper,
}


#: describes backend requirements in form
#: {'backend name': (('1st package name in pypi', '1st package import name'), ...)}
LANGUAGE_REQUIREMENTS = {
    "python": (),
    "javascript": (),
    "go": (("sphinxcontrib-golangdomain", "sphinxcontrib.golangdomain"),),
    "dotnet": (("sphinxcontrib-dotnetdomain", "sphinxcontrib.dotnetdomain"),),
}  # type: Dict[str, Sequence[Tuple[str, str]]]
