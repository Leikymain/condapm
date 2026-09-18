from __future__ import annotations

from pathlib import Path

from condapm.application.exceptions import EnvironmentNotFoundError
from condapm.application.ports import (
    CondaAdapterProtocol,
    LinkEnvironmentConfigStoreProtocol,
)
from condapm.domain.project import Project


class LinkEnvironmentUseCase:
    def __init__(
        self,
        config_store: LinkEnvironmentConfigStoreProtocol,
        conda_adapter: CondaAdapterProtocol,
    ) -> None:
        self._config_store = config_store
        self._conda_adapter = conda_adapter

    def execute(self, project_path: Path, env_name: str) -> None:
        Project(path=project_path)
        if not self._conda_adapter.environment_exists(env_name):
            raise EnvironmentNotFoundError(env_name)
        self._config_store.add_link(project_path, env_name)
