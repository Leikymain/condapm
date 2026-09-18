from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import platformdirs

from condapm.domain.link import ProjectEnvironmentLink


@dataclass
class LinkEntry:
    project_path: str
    env_name: str


@dataclass
class ConfigData:
    links: list[LinkEntry]


class ConfigStore:
    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path(platformdirs.user_config_dir("condapm"))
        self._config_dir = config_dir
        self._config_path = config_dir / "config.json"
        config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> dict[str, Any]:
        data = self._load_raw()
        return {
            "links": [
                {"project_path": e.project_path, "env_name": e.env_name}
                for e in data.links
            ],
        }

    def _load_raw(self) -> ConfigData:
        if not self._config_path.exists():
            return ConfigData(links=[])

        try:
            config: dict[str, Any] = json.loads(
                self._config_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            return ConfigData(links=[])

        config = self._migrate(config)

        links = [
            LinkEntry(project_path=link["project_path"], env_name=link["env_name"])
            for link in config.get("links", [])
        ]
        return ConfigData(links=links)

    @staticmethod
    def _migrate(config: dict[str, Any]) -> dict[str, Any]:
        if "proyects" in config:
            config = {
                "links": [
                    {"project_path": path_str, "env_name": data["env_name"]}
                    for path_str, data in config["proyects"].items()
                ],
            }
        elif any("proyect_path" in link for link in config.get("links", [])):
            config["links"] = [
                {
                    "project_path": link.get("project_path")
                    or link.get("proyect_path", ""),
                    "env_name": link["env_name"],
                }
                for link in config.get("links", [])
            ]
        config.setdefault("links", [])
        return config

    def save(self, config: dict[str, Any]) -> None:
        links = [
            LinkEntry(project_path=link["project_path"], env_name=link["env_name"])
            for link in config.get("links", [])
        ]
        self._save(ConfigData(links=links))

    def _save(self, data: ConfigData) -> None:
        fd, tmp_str = tempfile.mkstemp(
            dir=self._config_dir, suffix=".tmp", prefix=".config_"
        )
        tmp_path = Path(tmp_str)
        try:
            os.close(fd)
            payload = {
                "links": [
                    {"project_path": e.project_path, "env_name": e.env_name}
                    for e in data.links
                ],
            }
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp_path.replace(self._config_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

    # --- Many-to-many link methods ---

    def add_link(self, project_path: Path, env_name: str) -> None:
        ProjectEnvironmentLink(project_path=project_path, env_name=env_name)
        data = self._load_raw()
        path_str = str(project_path)
        for link in data.links:
            if link.project_path == path_str and link.env_name == env_name:
                return
        data.links.append(LinkEntry(project_path=path_str, env_name=env_name))
        self._save(data)

    def remove_link(self, project_path: Path, env_name: str) -> None:
        data = self._load_raw()
        path_str = str(project_path)
        data.links = [
            link
            for link in data.links
            if not (link.project_path == path_str and link.env_name == env_name)
        ]
        self._save(data)

    def list_links(self) -> list[ProjectEnvironmentLink]:
        data = self._load_raw()
        links = []
        for link in data.links:
            p = Path(link.project_path)
            if not p.is_absolute():
                continue
            try:
                links.append(
                    ProjectEnvironmentLink(project_path=p, env_name=link.env_name)
                )
            except ValueError:
                continue
        return links

    def envs_for_project(self, project_path: Path) -> list[str]:
        path_str = str(project_path)
        data = self._load_raw()
        return [link.env_name for link in data.links if link.project_path == path_str]

    def projects_for_env(self, env_name: str) -> list[Path]:
        data = self._load_raw()
        return [
            Path(link.project_path) for link in data.links if link.env_name == env_name
        ]
