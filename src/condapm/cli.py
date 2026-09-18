from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from condapm.application import (
    CheckLinksUseCase,
    CreateEnvironmentUseCase,
    EnvironmentAction,
    EnvironmentNotFoundError,
    LinkEnvironmentUseCase,
    LinkNotFoundError,
    ListPackagesUseCase,
    ListProjectsUseCase,
    UnlinkEnvironmentUseCase,
)
from condapm.infrastructure.config_store import ConfigStore
from condapm.infrastructure.conda_adapter import CondaAdapter
from condapm.infrastructure.pip_adapter import PipAdapter
from condapm.infrastructure.vscode_adapter import VSCodeAdapter, VSCodeNotFoundError
from condapm.ui.formatters import render_packages_table, render_projects_table
from condapm.ui.manual import render_command_page, render_full_manual
from rich.console import Console

app = typer.Typer(help="Conda Project Manager")


@app.callback()
def callback() -> None:
    pass


@app.command("list-projects")
def list_projects(
    filter_pip: str | None = typer.Option(
        None,
        "--filter-pip",
        help="Filter projects by installed pip package (e.g. fastapi, fastapi>=0.100)",
    ),
) -> None:
    use_case = ListProjectsUseCase(
        config_store=ConfigStore(),
        conda_adapter=CondaAdapter(),
        pip_adapter=PipAdapter(),
    )
    statuses = use_case.execute(pip_filter=filter_pip)
    if filter_pip and not statuses:
        typer.echo(f"No projects found with package '{filter_pip}' installed.")
        return
    render_projects_table(statuses)


@app.command("create")
def create(
    env_name: str = typer.Argument(..., help="Name for the conda environment"),
    python_version: str = typer.Option(
        ..., "--python", help="Python version (e.g. 3.13)"
    ),
) -> None:
    project_path = Path.cwd()
    config_store = ConfigStore()
    use_case = CreateEnvironmentUseCase(
        config_store=config_store,
        conda_adapter=CondaAdapter(),
    )
    try:
        action = use_case.execute(
            project_path=project_path,
            env_name=env_name,
            python_version=python_version,
        )
    except subprocess.CalledProcessError as exc:
        typer.echo(
            f"✗ Conda command failed (exit {exc.returncode}). Check conda output above.",
            err=True,
        )
        raise typer.Exit(code=1)
    except (ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        typer.echo(f"✗ Error: {exc}", err=True)
        raise typer.Exit(code=1)

    if action == EnvironmentAction.CREATED:
        typer.echo(f"✓ Conda environment '{env_name}' created successfully.")
    else:
        typer.echo(
            f"✓ Conda environment '{env_name}' already exists — linked to project."
        )
    typer.echo(f"✓ Linked to project '{project_path}'.")
    typer.echo(f"✓ Config saved to {config_store.config_path}")


@app.command("open")
def open_project(
    project_filter: str | None = typer.Argument(
        None, help="Substring to filter project paths (omit to list all)"
    ),
) -> None:
    config_store = ConfigStore()
    all_links = config_store.list_links()
    projects: list[Path] = list(dict.fromkeys(lnk.project_path for lnk in all_links))

    if project_filter:
        projects = [p for p in projects if project_filter.lower() in str(p).lower()]
        if not projects:
            typer.echo(
                typer.style(
                    f"✗ No projects found matching '{project_filter}'",
                    fg=typer.colors.RED,
                ),
                err=True,
            )
            raise typer.Exit(code=1)

    if not projects:
        typer.echo("No projects registered. Run 'condapm create' to link a project.")
        return

    if len(projects) == 1:
        project_path = projects[0]
    else:
        typer.echo("Registered projects:")
        for i, p in enumerate(projects, 1):
            typer.echo(f"  {i}. {p}")
        choice = typer.prompt("Select a project number", type=int)
        if choice < 1 or choice > len(projects):
            typer.echo(
                typer.style(f"✗ Invalid selection: {choice}", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(code=1)
        project_path = projects[choice - 1]

    envs = config_store.envs_for_project(project_path)
    if not envs:
        typer.echo(
            typer.style(
                f"⚠ No environments linked to '{project_path}'",
                fg=typer.colors.YELLOW,
            ),
            err=True,
        )
        raise typer.Exit(code=1)

    if len(envs) == 1:
        env_name = envs[0]
    else:
        typer.echo(f"Environments linked to '{project_path}':")
        for i, e in enumerate(envs, 1):
            typer.echo(f"  {i}. {e}")
        choice = typer.prompt("Select an environment number", type=int)
        if choice < 1 or choice > len(envs):
            typer.echo(
                typer.style(f"✗ Invalid selection: {choice}", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(code=1)
        env_name = envs[choice - 1]

    conda = CondaAdapter()
    known_envs = conda.list_environments()
    if env_name not in known_envs:
        typer.echo(
            typer.style(
                f"⚠ Environment '{env_name}' no longer exists in conda",
                fg=typer.colors.YELLOW,
            ),
            err=True,
        )
        raise typer.Exit(code=1)

    env_dir = known_envs[env_name]
    try:
        VSCodeAdapter().open_project(project_path, env_name, env_dir)
    except VSCodeNotFoundError as exc:
        typer.echo(typer.style(f"✗ Error: {exc}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)

    typer.echo(f"✓ Opened '{project_path}' in VS Code with environment '{env_name}'.")


@app.command("link")
def link_env(
    env_name: str = typer.Argument(..., help="Name of an existing conda environment"),
) -> None:
    project_path = Path.cwd()
    use_case = LinkEnvironmentUseCase(
        config_store=ConfigStore(),
        conda_adapter=CondaAdapter(),
    )
    try:
        use_case.execute(project_path=project_path, env_name=env_name)
    except EnvironmentNotFoundError as exc:
        typer.echo(typer.style(f"✗ Error: {exc}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
    except ValueError as exc:
        typer.echo(typer.style(f"✗ Error: {exc}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)

    typer.echo(f"✓ Linked '{env_name}' to project '{project_path}'.")


@app.command("unlink")
def unlink_env(
    env_name: str = typer.Argument(..., help="Name of the conda environment to unlink"),
) -> None:
    project_path = Path.cwd()
    use_case = UnlinkEnvironmentUseCase(config_store=ConfigStore())
    try:
        use_case.execute(project_path=project_path, env_name=env_name)
    except LinkNotFoundError as exc:
        typer.echo(typer.style(f"⚠ Warning: {exc}", fg=typer.colors.YELLOW), err=True)
        raise typer.Exit(code=1)

    typer.echo(f"✓ Unlinked '{env_name}' from project '{project_path}'.")


@app.command("list-packages")
def list_packages(
    env_name: str = typer.Argument(..., help="Name of the conda environment"),
) -> None:
    use_case = ListPackagesUseCase(
        conda_adapter=CondaAdapter(),
        pip_adapter=PipAdapter(),
    )
    try:
        packages = use_case.execute(env_name)
    except EnvironmentNotFoundError as exc:
        typer.echo(typer.style(f"✗ Error: {exc}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
    except RuntimeError as exc:
        typer.echo(typer.style(f"✗ Error: {exc}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)
    render_packages_table(packages, env_name)


@app.command("doctor")
def doctor(
    fix: bool = typer.Option(False, "--fix", help="Remove broken links from config"),
) -> None:
    from rich.console import Console
    from rich.table import Table

    config_store = ConfigStore()
    use_case = CheckLinksUseCase(
        config_store=config_store,
        conda_adapter=CondaAdapter(),
    )
    broken = use_case.execute()

    if not broken:
        typer.echo(typer.style("✓ All links are healthy.", fg=typer.colors.GREEN))
        return

    console = Console()
    table = Table(show_header=True)
    table.add_column("Project Path")
    table.add_column("Conda Env")
    table.add_column("Problem")
    _labels = {
        "env_missing": "Conda env not found",
        "path_missing": "Directory not found",
        "both_missing": "Directory and conda env not found",
    }
    for link in broken:
        table.add_row(str(link.project_path), link.env_name, _labels[link.reason])
    console.print(table)

    if fix:
        for link in broken:
            config_store.remove_link(link.project_path, link.env_name)
        typer.echo(f"✓ Fixed {len(broken)} broken link(s).")

    raise typer.Exit(code=1)


@app.command("man")
def man(
    command: str | None = typer.Argument(
        None, help="Command name to show manual for (omit for full manual)"
    ),
) -> None:
    console = Console()
    if command is None:
        console.print(render_full_manual())
    else:
        try:
            renderable = render_command_page(command)
        except KeyError:
            typer.echo(
                typer.style(f"✗ Unknown command: {command}", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(code=1)
        console.print(renderable)
