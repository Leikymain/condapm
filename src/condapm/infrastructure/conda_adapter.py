from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from condapm.domain.link import _SAFE_ENV_NAME


def _find_conda_executable() -> str:
    if conda := shutil.which("conda"):
        return conda
    if conda_exe := os.environ.get("CONDA_EXE"):
        p = Path(conda_exe)
        if p.is_file() and p.name in {"conda", "conda.exe", "conda.bat"}:
            return str(p)
    home = Path.home()
    if os.name == "nt":
        candidates = [
            home / "anaconda3" / "Scripts" / "conda.exe",
            home / "miniconda3" / "Scripts" / "conda.exe",
            home / "miniforge3" / "Scripts" / "conda.exe",
            home / "mambaforge" / "Scripts" / "conda.exe",
            Path("C:/ProgramData/anaconda3/Scripts/conda.exe"),
            Path("C:/ProgramData/miniconda3/Scripts/conda.exe"),
        ]
    else:
        candidates = [
            home / "anaconda3" / "bin" / "conda",
            home / "miniconda3" / "bin" / "conda",
            home / "miniforge3" / "bin" / "conda",
            home / "mambaforge" / "bin" / "conda",
            Path("/opt/conda/bin/conda"),
            Path("/opt/anaconda3/bin/conda"),
        ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError(
        "conda executable not found. Install conda and ensure it is on PATH, "
        "or run 'conda init' to register it with your shell."
    )


class CondaAdapter:
    def __init__(
        self,
        timeout: int = 10,
        create_timeout: int = 300,
        conda_executable: str | None = None,
    ) -> None:
        self._conda = (
            conda_executable
            if conda_executable is not None
            else _find_conda_executable()
        )
        self._timeout = timeout
        self._create_timeout = create_timeout

    def list_environments(self) -> dict[str, Path]:
        result = subprocess.run(
            [self._conda, "env", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=self._timeout,
        )
        result.check_returncode()
        try:
            data: dict[str, list[str]] = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Unexpected output from conda (could not parse JSON): {result.stdout[:200]!r}"
            ) from exc
        return {Path(p).name: Path(p) for p in data["envs"]}

    def create_environment(self, env_name: str, python_version: str) -> None:
        if not _SAFE_ENV_NAME.fullmatch(env_name):
            raise ValueError(
                f"env_name '{env_name}' contains invalid characters. "
                "Only letters, digits, dots, underscores, and hyphens are allowed."
            )
        result = subprocess.run(
            [self._conda, "create", "-n", env_name, f"python={python_version}", "-y"],
            capture_output=True,
            text=True,
            timeout=self._create_timeout,
        )
        try:
            result.check_returncode()
        except subprocess.CalledProcessError:
            if "PackagesNotFoundError" in (result.stderr or ""):
                raise RuntimeError(
                    f"Python version '{python_version}' passed format validation, "
                    "but conda could not find a matching package. "
                    f"Use 'conda search python={python_version}' to check "
                    "available versions."
                )
            raise

    def environment_exists(self, env_name: str) -> bool:
        try:
            return env_name in self.list_environments()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
