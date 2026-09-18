from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


@dataclass
class ManualPage:
    synopsis: str
    description: str
    options: list[tuple[str, str]] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    notes: str = ""


def _build_page_content(page: ManualPage) -> RenderableType:
    parts: list[RenderableType] = []
    parts.append(Rule("SYNOPSIS", style="bold blue"))
    parts.append(Padding(Text(page.synopsis, style="bold"), (0, 0, 1, 2)))
    parts.append(Rule("DESCRIPTION", style="dim"))
    parts.append(Padding(Text(page.description), (0, 0, 1, 2)))
    if page.options:
        parts.append(Rule("OPTIONS", style="bold blue"))
        t = Table(show_header=False, box=None, padding=(0, 2, 0, 2))
        t.add_column("flag", style="cyan")
        t.add_column("desc")
        for flag, desc in page.options:
            t.add_row(flag, desc)
        parts.append(t)
    if page.examples:
        parts.append(Rule("EXAMPLES", style="bold blue"))
        for ex in page.examples:
            parts.append(Text(f"  $ {ex}", style="bold green"))
    if page.notes:
        parts.append(Rule("NOTES", style="dim"))
        parts.append(Padding(Text(page.notes), (0, 0, 0, 2)))
    return Group(*parts)


MANUAL: dict[str, ManualPage] = {
    "list-projects": ManualPage(
        synopsis="condapm list-projects [--filter-pip PACKAGE]",
        description="List all registered projects with linked conda environments and pip packages.",
        options=[
            (
                "--filter-pip PACKAGE",
                "Filter to projects whose env contains PACKAGE (supports version constraints e.g. fastapi>=0.100)",
            )
        ],
        examples=[
            "condapm list-projects",
            "condapm list-projects --filter-pip fastapi",
        ],
        notes="Environments that no longer exist in conda are shown with a warning symbol.",
    ),
    "create": ManualPage(
        synopsis="condapm create ENV_NAME --python VERSION",
        description="Create a new conda environment and link it to the current directory. If the environment already exists, it is linked without re-creating.",
        options=[
            ("ENV_NAME", "Name for the new conda environment"),
            ("--python VERSION", "Python version to use (e.g. 3.13)"),
        ],
        examples=["condapm create my-env --python 3.13"],
    ),
    "open": ManualPage(
        synopsis="condapm open [FILTER]",
        description="Open VS Code on a registered project. FILTER is an optional substring to match against project paths.",
        options=[("FILTER", "Optional substring to filter project paths")],
        examples=["condapm open", "condapm open my-app"],
        notes="If multiple projects match, you are prompted to select one.",
    ),
    "link": ManualPage(
        synopsis="condapm link ENV_NAME",
        description="Link an existing conda environment to the current directory without creating a new one.",
        options=[("ENV_NAME", "Name of an existing conda environment")],
        examples=["condapm link my-env"],
    ),
    "unlink": ManualPage(
        synopsis="condapm unlink ENV_NAME",
        description="Remove the association between the current directory and a conda environment.",
        options=[("ENV_NAME", "Name of the conda environment to unlink")],
        examples=["condapm unlink my-env"],
        notes="Does not delete the conda environment itself.",
    ),
    "list-packages": ManualPage(
        synopsis="condapm list-packages ENV_NAME",
        description="List pip packages installed in the named conda environment.",
        options=[
            ("ENV_NAME", "Name of the conda environment to inspect"),
        ],
        examples=[
            "condapm list-packages my-env",
        ],
        notes="Exits with code 1 if the environment does not exist or conda is unavailable.",
    ),
    "doctor": ManualPage(
        synopsis="condapm doctor [--fix]",
        description="Scan all registered links and report broken ones (missing directory or missing conda environment).",
        options=[("--fix", "Remove each broken link from the config after reporting")],
        examples=["condapm doctor", "condapm doctor --fix"],
        notes="Exits with code 1 if any broken links are found.",
    ),
    "man": ManualPage(
        synopsis="condapm man [COMMAND]",
        description="Show the manual page for a command, or the full manual if no command is given.",
        options=[
            (
                "COMMAND",
                "Optional command name (list-projects, create, open, link, unlink, list-packages, doctor, man)",
            )
        ],
        examples=["condapm man", "condapm man create"],
    ),
}


def render_command_page(name: str) -> RenderableType:
    page = MANUAL[name]  # KeyError propagates — intentional
    return Panel(
        _build_page_content(page),
        title=f"condapm {name}",
        title_align="left",
        expand=False,
    )


def render_full_manual() -> RenderableType:
    return Group(*(render_command_page(name) for name in MANUAL))
