from __future__ import annotations

from enum import Enum
from pathlib import Path

from condapm.application.ports import CondaAdapterProtocol, ConfigStoreProtocol
from condapm.domain.environment import CondaEnvironment
from condapm.domain.project import Project


class EnvironmentAction(Enum):
    CREATED = "created"
    LINKED = "linked"


class CreateEnvironmentUseCase:
    def __init__(
        self,
        config_store: ConfigStoreProtocol,
        conda_adapter: CondaAdapterProtocol,
    ) -> None:
        self._config_store = config_store
        self._conda_adapter = conda_adapter

    def execute(
        self, project_path: Path, env_name: str, python_version: str
    ) -> EnvironmentAction:
        # Validate inputs — no side effects yet.
        Project(path=project_path)
        CondaEnvironment(name=env_name, python_version=python_version)

        if self._conda_adapter.environment_exists(env_name):
            # Env already exists — link without re-creating.
            self._config_store.add_link(project_path, env_name)
            return EnvironmentAction.LINKED

        # New env: create first, then link.
        self._conda_adapter.create_environment(env_name, python_version)
        self._config_store.add_link(project_path, env_name)
        return EnvironmentAction.CREATED
