from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from condapm.domain.pip_package import PipPackage


class PipAdapter:
    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout

    def list_packages(self, env_path: Path) -> list[PipPackage]:
        if sys.platform == "win32":
            pip_exe = env_path / "Scripts" / "pip.exe"
        else:
            pip_exe = env_path / "bin" / "pip"
        try:
            result = subprocess.run(
                [str(pip_exe), "list", "--not-required", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except FileNotFoundError:
            return []
        result.check_returncode()
        data: list[dict[str, str]] = json.loads(result.stdout)
        return [PipPackage(name=p["name"], version=p["version"]) for p in data]
