from .base import UnknownType
from .dotnet import DotNetNamespace, DotNetClass
from .python import PythonModule, PythonClass, PythonFunction


def classify(obj, obj_type):
    if 'type' not in obj:
        return ''

    if obj_type == 'python':
        if obj['type'] == 'module':
            return PythonModule(obj)
        if obj['type'] == 'class':
            return PythonClass(obj)
        if obj['type'] == 'function':
            return PythonFunction(obj)
    if obj_type == 'dotnet':
        if obj['type'] == 'Class':
            return DotNetClass(obj)
        if obj['type'] == 'Namespace':
            return DotNetNamespace(obj)
    return UnknownType(obj)
