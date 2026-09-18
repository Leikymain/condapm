from __future__ import annotations

from condapm.application.exceptions import EnvironmentNotFoundError
from condapm.application.ports import CondaAdapterProtocol, PipAdapterProtocol
from condapm.domain.pip_package import PipPackage


class ListPackagesUseCase:
    def __init__(
        self,
        conda_adapter: CondaAdapterProtocol,
        pip_adapter: PipAdapterProtocol,
    ) -> None:
        self._conda = conda_adapter
        self._pip = pip_adapter

    def execute(self, env_name: str) -> list[PipPackage]:
        if not env_name.strip():
            raise ValueError("env_name cannot be empty or whitespace-only")
        envs = self._conda.list_environments()
        if env_name not in envs:
            raise EnvironmentNotFoundError(env_name)
        return self._pip.list_packages(envs[env_name])
