from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from condapm.domain.pip_package import PipPackage


@dataclass(frozen=True)
class ProjectStatus:
    project_path: Path
    env_name: str
    env_exists: bool
    packages: list[PipPackage] | None
