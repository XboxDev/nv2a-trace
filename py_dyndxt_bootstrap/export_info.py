"""Encapsulates information about a DLL export."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExportInfo:
    """Encapsulates information about a DLL export."""

    ordinal: int
    name: Optional[str] = None
    address: Optional[int] = None
