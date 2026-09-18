from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipPackage:
    name: str
    version: str
