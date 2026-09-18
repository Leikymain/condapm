from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Project:
    path: Path

    def __post_init__(self) -> None:
        if not self.path.exists():
            raise ValueError(f"Path '{self.path}' does not exist")
