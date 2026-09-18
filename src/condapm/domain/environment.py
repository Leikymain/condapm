import re
from dataclasses import dataclass

_VERSION_RE = re.compile(r"^\d+\.\d{1,2}(\.\d{1,2})?(-[A-Za-z0-9._-]+)*$")


@dataclass(frozen=True)
class CondaEnvironment:
    name: str
    python_version: str

    def __post_init__(self) -> None:
        if not _VERSION_RE.match(self.python_version):
            raise ValueError(
                f"Invalid Python version '{self.python_version}'. "
                "Valid formats: 3.11, 3.12, 3.13, 3.13.1 "
                "(optional suffix: 3.13-alpine, 3.13.14-slim, 3.9.18-h123_0)"
            )
