from __future__ import annotations

from pathlib import Path


class EnvironmentNotFoundError(Exception):
    def __init__(self, env_name: str) -> None:
        super().__init__(f"Environment '{env_name}' does not exist in conda.")


class LinkNotFoundError(Exception):
    def __init__(self, project_path: Path, env_name: str) -> None:
        super().__init__(f"No link between '{project_path}' and '{env_name}'.")
