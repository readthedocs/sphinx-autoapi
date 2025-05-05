from typing import TypeAlias
import typing
import typing_extensions

MyTypeAliasA: TypeAlias = tuple[str, int]
type MyTypeAliasB = tuple[str, int]
MyTypeAliasC: typing.TypeAlias = tuple[str, int]
MyTypeAliasD: typing_extensions.TypeAlias = tuple[str, int]
