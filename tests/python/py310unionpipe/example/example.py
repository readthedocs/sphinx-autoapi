from pathlib import Path
from typing import Optional, Union


def simple(p: Path):
    """This is OK"""


def optional(p: Optional[Path]):
    """This is OK"""


def union(p: Union[Path, None]):
    """This is OK"""


def pipe(p: Path | None):
    """This is OK"""
