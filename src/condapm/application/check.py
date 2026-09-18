from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from condapm.application.ports import (
    CheckLinksConfigStoreProtocol,
    CondaAdapterProtocol,
)


@dataclass
class BrokenLink:
    project_path: Path
    env_name: str
    reason: str  # "env_missing" | "path_missing" | "both_missing"


class CheckLinksUseCase:
    def __init__(
        self,
        config_store: CheckLinksConfigStoreProtocol,
        conda_adapter: CondaAdapterProtocol,
    ) -> None:
        self._config_store = config_store
        self._conda_adapter = conda_adapter

    def execute(self) -> list[BrokenLink]:
        broken = []
        for link in self._config_store.list_links():
            path_ok = link.project_path.exists()
            env_ok = self._conda_adapter.environment_exists(link.env_name)
            if path_ok and env_ok:
                continue
            if not path_ok and not env_ok:
                reason = "both_missing"
            elif not path_ok:
                reason = "path_missing"
            else:
                reason = "env_missing"
            broken.append(BrokenLink(link.project_path, link.env_name, reason))
        return broken
