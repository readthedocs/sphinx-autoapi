from .base import UnknownType
from .dotnet import (
    DotNetNamespace, DotNetClass, DotNetMethod, DotNetProperty,
    DotNetEnum, DotNetConstructor, DotNetStruct, DotNetInterface,
    DotNetDelegate, DotNetField, DotNetEvent
    )
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
        if obj['type'] == 'Property':
            return DotNetProperty(obj)
        if obj['type'] == 'Method':
            return DotNetMethod(obj)
        if obj['type'] == 'Enum':
            return DotNetEnum(obj)
        if obj['type'] == 'Constructor':
            return DotNetConstructor(obj)
        if obj['type'] == 'Struct':
            return DotNetStruct(obj)
        if obj['type'] == 'Interface':
            return DotNetInterface(obj)
        if obj['type'] == 'Delegate':
            return DotNetDelegate(obj)
        if obj['type'] == 'Field':
            return DotNetField(obj)
        if obj['type'] == 'Event':
            return DotNetEvent(obj)
    return UnknownType(obj)
