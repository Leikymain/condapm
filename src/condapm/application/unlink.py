from __future__ import annotations

from pathlib import Path

from condapm.application.exceptions import LinkNotFoundError
from condapm.application.ports import LinkEnvironmentConfigStoreProtocol


class UnlinkEnvironmentUseCase:
    def __init__(
        self,
        config_store: LinkEnvironmentConfigStoreProtocol,
    ) -> None:
        self._config_store = config_store

    def execute(self, project_path: Path, env_name: str) -> None:
        existing = self._config_store.envs_for_project(project_path)
        if env_name not in existing:
            raise LinkNotFoundError(project_path, env_name)
        self._config_store.remove_link(project_path, env_name)
