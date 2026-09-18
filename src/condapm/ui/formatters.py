from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from condapm.domain.pip_package import PipPackage
from condapm.domain.status import ProjectStatus

_console = Console()

_SYSTEM_PACKAGES = {
    # Originales
    "pip",
    "setuptools",
    "wheel",
    "pkg-resources",
    "pkg_resources",
    # Herramientas de entorno/Conda/Falsos positivos
    "condapm",
    "mysql",
    "types-setuptools",
    # Ruido de tipado/infraestructura interna (Pydantic/Typing)
    "annotated-doc",
    "annotated-types",
    "typing_extensions",
    "typing-inspection",
}


def _short_path(p: Path) -> str:
    parts = p.parts
    if len(parts) <= 3:
        return str(p)
    return "..." + str(Path(*parts[-3:]))


def _render_env_cell(status: ProjectStatus) -> str:
    if not status.env_exists:
        return f"⚠ {status.env_name} (not found)"
    return status.env_name


def _render_packages_cell(status: ProjectStatus) -> str:
    if not status.env_exists:
        return "—"
    if status.packages is None:
        return "⏱ timeout"
    if not status.packages:
        return "(none)"
    parts = [
        f"{p.name}=={p.version}"
        for p in status.packages
        if p.name.lower() not in _SYSTEM_PACKAGES
    ]
    if not parts:
        return "(none)"
    lines = [", ".join(parts[i : i + 4]) for i in range(0, len(parts), 4)]
    return "\n".join(lines)


def render_packages_table(packages: list[PipPackage], env_name: str) -> None:
    user_packages = sorted(
        [p for p in packages if p.name.lower() not in _SYSTEM_PACKAGES],
        key=lambda p: p.name.lower(),
    )
    if not user_packages:
        _console.print(f"No user packages installed in '{env_name}'.")
        return
    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("Package")
    table.add_column("Version")
    for pkg in user_packages:
        table.add_row(pkg.name, pkg.version)
    _console.print(table)


def render_projects_table(statuses: list[ProjectStatus]) -> None:
    if not statuses:
        _console.print(
            "No projects registered. Run 'condapm create' to link a project."
        )
        return

    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("Project", overflow="ellipsis", no_wrap=True)
    table.add_column("Conda Env")
    table.add_column("Pip Packages")

    for status in statuses:
        table.add_row(
            _short_path(status.project_path),
            _render_env_cell(status),
            _render_packages_cell(status),
        )

    _console.print(table)
