from typing import NamedTuple

import griffe


class ArgInfo(NamedTuple):
    prefix: str | None
    name: str | None
    annotation: str | None
    default: str | None


class TypeParamInfo(NamedTuple):
    prefix: str | None
    name: str | None
    annotation: str | None


def get_args_info(parameters: griffe.Parameters) -> list[ArgInfo]:
    args_info = []

    seen_pos_only = False
    seen_kw_only = False
    for param in parameters.values():
        prefix = None
        if param.kind == griffe.ParameterKind.positional_only and not seen_pos_only:
            args_info.append(ArgInfo("/", None, None, None))
            seen_pos_only = True
        if param.kind == griffe.ParameterKind.keyword_only and not seen_kw_only:
            args_info.append(ArgInfo("*", None, None, None))
            seen_kw_only = True

        if param.kind == griffe.ParameterKind.var_positional:
            prefix = "*"
        elif param.kind == griffe.ParameterKind.var_keyword:
            prefix = "**"

        name = param.name
        # TODO: What if annotation is an Expr?
        annotation = param.annotation or None
        # TODO: What if default is an Expr?
        default = param.default or None

        args_info.append(ArgInfo(prefix, name, annotation, default))

    return args_info


def get_type_params_info(type_parameters: griffe.TypeParameters) -> list[TypeParamInfo]:
    type_params_info = []

    # TODO: Need to use constraints and default
    for type_param in type_parameters.values():
        prefix = None
        if type_param.kind == griffe.TypeParameterKind.type_var:
            type_params_info.append(TypeParamInfo(None, type_param.name, type_param.bound))
        if type_param.kind == griffe.TypeParameterKind.type_var_tuple:
            type_params_info.append(TypeParamInfo("*", type_param.name, type_param.bound))
        elif type_param.kind == griffe.TypeParameterKind.param_spec:
            type_params_info.append(TypeParamInfo("**", type_param.name, type_param.bound))

    return type_params_info


def is_abstract(obj: griffe.Class) -> bool:
    if any(base.path == "abc.ABC" for base in obj.bases):
        return True

    # TODO: If metaclass is ABCMeta
    return False


def is_exception(obj: griffe.Class) -> bool:
    return any(
        base.path in ("builtins.BaseException", "builtins.Exception")
        for base in obj.mro()
    )


def relevant_bases(obj: griffe.Class) -> list[str]:
    return [
        base.path
        for base in obj.resolved_bases
        if base.path not in ("builtins.object", "builtins.type")
    ]
