import re
from dataclasses import dataclass
from pathlib import Path

_SAFE_ENV_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class ProjectEnvironmentLink:
    project_path: Path
    env_name: str

    def __post_init__(self) -> None:
        if not self.project_path.parts:
            raise ValueError("project_path cannot be empty")
        if not self.env_name:
            raise ValueError("env_name cannot be empty")
        if not _SAFE_ENV_NAME.fullmatch(self.env_name):
            raise ValueError(
                f"env_name '{self.env_name}' contains invalid characters. "
                "Only letters, digits, dots, underscores, and hyphens are allowed."
            )
