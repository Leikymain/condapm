from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from condapm.application.ports import (
    CondaAdapterProtocol,
    ConfigStoreProtocol,
    PipAdapterProtocol,
)
from condapm.domain.pip_package import PipPackage
from condapm.domain.status import ProjectStatus

_FILTER_RE = re.compile(r"^([A-Za-z0-9_.\-]+)([><=!].+)?$")


def _matches_pip_filter(packages: list[PipPackage], pip_filter: str) -> bool:
    m = _FILTER_RE.match(pip_filter.strip())
    if not m:
        return False
    name_part = m.group(1).lower()
    version_spec = m.group(2)
    if version_spec is not None:
        try:
            spec = SpecifierSet(version_spec)
        except InvalidSpecifier:
            return False  # malformed specifier → nothing matches
    for pkg in packages:
        if name_part not in pkg.name.lower():
            continue
        if version_spec is None:
            return True
        try:
            if Version(pkg.version) in spec:
                return True
        except InvalidVersion:
            continue  # skip unparseable package version, keep checking others
    return False


class ListProjectsUseCase:
    def __init__(
        self,
        config_store: ConfigStoreProtocol,
        conda_adapter: CondaAdapterProtocol,
        pip_adapter: PipAdapterProtocol,
    ) -> None:
        self._config_store = config_store
        self._conda_adapter = conda_adapter
        self._pip_adapter = pip_adapter

    def execute(self, pip_filter: str | None = None) -> list[ProjectStatus]:
        try:
            all_envs = self._conda_adapter.list_environments()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            all_envs = {}

        projects = self._config_store.list_links()

        existing_env_names = {p.env_name for p in projects if p.env_name in all_envs}

        def fetch(env_name: str) -> tuple[str, list[PipPackage] | None]:
            try:
                return env_name, self._pip_adapter.list_packages(all_envs[env_name])
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                return env_name, None

        packages_map: dict[str, list[PipPackage] | None] = {}
        if existing_env_names:
            with ThreadPoolExecutor() as pool:
                for name, pkgs in pool.map(fetch, existing_env_names):
                    packages_map[name] = pkgs

        results = []
        for project in projects:
            env_name = project.env_name
            env_exists = env_name in all_envs
            packages = packages_map.get(env_name) if env_exists else None
            if pip_filter is not None:
                if packages is None or not _matches_pip_filter(packages, pip_filter):
                    continue
            results.append(
                ProjectStatus(
                    project_path=project.project_path,
                    env_name=env_name,
                    env_exists=env_exists,
                    packages=packages,
                )
            )
        return results
