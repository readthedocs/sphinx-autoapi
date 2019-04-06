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
