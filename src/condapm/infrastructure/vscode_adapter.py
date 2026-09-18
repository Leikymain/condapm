from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from condapm.domain.link import _SAFE_ENV_NAME


class VSCodeNotFoundError(Exception):
    pass


class VSCodeAdapter:
    def __init__(self, code_executable: str = "code") -> None:
        self._code = code_executable

    def open_project(
        self, project_path: Path, env_name: str, env_dir: Path | None = None
    ) -> None:
        code_path = shutil.which(self._code)
        if not code_path:
            raise VSCodeNotFoundError(
                f"VS Code CLI '{self._code}' not found on PATH. "
                "Install VS Code and ensure 'code' is in your PATH."
            )
        if not _SAFE_ENV_NAME.fullmatch(env_name):
            raise ValueError(
                f"env_name '{env_name}' contains invalid characters. "
                "Only letters, digits, dots, underscores, and hyphens are allowed."
            )
        self._configure_terminal(project_path, env_name, env_dir)
        env = os.environ.copy()
        if env_dir is not None:
            env["CONDA_PREFIX"] = str(env_dir)
            env["CONDA_DEFAULT_ENV"] = env_name
            scripts = (
                str(env_dir / "Scripts") if os.name == "nt" else str(env_dir / "bin")
            )
            env["PATH"] = scripts + os.pathsep + env.get("PATH", "")
        # On Windows, code is often a .cmd batch file; invoke it via cmd.exe
        # explicitly so we can keep shell=False and avoid shell injection.
        if os.name == "nt" and code_path.lower().endswith(".cmd"):
            cmd = ["cmd.exe", "/c", code_path, str(project_path)]
        else:
            cmd = [code_path, str(project_path)]
        subprocess.run(cmd, check=False, shell=False, env=env)

    def _configure_terminal(
        self, project_path: Path, env_name: str, env_dir: Path | None = None
    ) -> None:
        settings_dir = project_path / ".vscode"
        settings_dir.mkdir(exist_ok=True)
        settings_path = settings_dir / "settings.json"
        settings: dict[str, Any] = {}
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                settings = {}
        profile_name = f"conda-{env_name}"
        settings.setdefault("terminal.integrated.profiles.windows", {})[
            profile_name
        ] = {
            "source": "PowerShell",
            "args": ["-NoExit", "-Command", f"conda activate {env_name}"],
        }
        settings["terminal.integrated.defaultProfile.windows"] = profile_name
        settings.setdefault("terminal.integrated.profiles.linux", {})[profile_name] = {
            "path": "bash",
            "args": ["-l", "-c", f"conda activate {env_name} && exec bash"],
        }
        settings["terminal.integrated.defaultProfile.linux"] = profile_name
        settings.setdefault("terminal.integrated.profiles.osx", {})[profile_name] = {
            "path": "zsh",
            "args": ["-l", "-c", f"conda activate {env_name} && exec zsh"],
        }
        settings["terminal.integrated.defaultProfile.osx"] = profile_name
        if env_dir is not None:
            python_exe = (
                env_dir / "python.exe"
                if os.name == "nt"
                else env_dir / "bin" / "python"
            )
            settings["python.defaultInterpreterPath"] = str(python_exe)
            settings["python.terminal.activateEnvironment"] = True
        settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
