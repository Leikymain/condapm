# Conda Project Manager

A CLI tool to manage conda environments per project.

## What does it do?

**Problem:** You have many Python projects, each with its own conda environment. Managing them is tedious — you have to remember which environment goes with which project.

**Solution:** Conda Project Manager lets you:
1. See all your projects with their linked conda environments
2. Create a new conda environment and automatically link it to your current project
3. View the pip packages in each environment
4. Open VS Code on a project linked to a conda environment
5. Filter your project list by installed pip package
6. Link multiple environments to a project (and vice-versa)
7. Explicitly link an existing environment to a project with `link`
8. Remove a project↔environment association with `unlink`
9. List all pip packages installed in any named conda environment with `list-packages`

## Example Usage

```bash
# List all projects and their environments
$ condapm list-projects

┌──────────────────────────┬────────────────┬──────────────────────────────┐
│ Project                  │ Conda Env      │ Pip Packages                 │
├──────────────────────────┼────────────────┼──────────────────────────────┤
│ /home/dev/my-app         │ my-app-env     │ fastapi==0.111, pydantic==2.7│
│ /home/dev/data-science   │ ds-env         │ pandas==2.2, numpy==1.26     │
└──────────────────────────┴────────────────┴──────────────────────────────┘

# Create and link a new environment
$ cd /home/dev/my-new-project
$ condapm create my-env --python 3.13

✓ Conda environment 'my-env' created successfully.
✓ Linked to project '/home/dev/my-new-project'.
✓ Config saved to ~/.config/condapm/config.json

# Link an already-existing environment to a second project
$ cd /home/dev/second-project
$ condapm create my-env --python 3.13

✓ Conda environment 'my-env' already exists — linked to project.
✓ Linked to project '/home/dev/second-project'.
✓ Config saved to ~/.config/condapm/config.json

# Open VS Code on a project by name — activates the linked conda env in the terminal
$ condapm open my-app

✓ Opened '/home/dev/my-app' in VS Code with environment 'my-app-env'.

# Filter by substring — prompts when multiple projects match
$ condapm open data

Registered projects:
  1. /home/dev/data-science
  2. /home/dev/data-tools
Select a project number: 1
✓ Opened '/home/dev/data-science' in VS Code with environment 'ds-env'.

# Omit the filter to list all registered projects
$ condapm open

# Filter project list by installed pip package
$ condapm list-projects --filter-pip fastapi

# (shows only projects that have fastapi installed)

# Version constraint filtering
$ condapm list-projects --filter-pip "fastapi>=0.100"

# Explicitly link an existing conda env to the current project
$ cd /home/dev/my-app
$ condapm link my-app-env

✓ Linked 'my-app-env' to project '/home/dev/my-app'.

# Remove the link between the current project and an env
$ condapm unlink my-app-env

✓ Unlinked 'my-app-env' from project '/home/dev/my-app'.

# List pip packages installed in a named conda environment
$ condapm list-packages my-app-env

┌──────────────┬──────────┐
│ Package      │ Version  │
├──────────────┼──────────┤
│ fastapi      │ 0.110.0  │
│ httpx        │ 0.27.0   │
└──────────────┴──────────┘
```

## Key Features

- ✅ Display projects with their conda environments
- ✅ Create new conda environments with specified Python version
- ✅ Auto-link environments to projects
- ✅ Link one environment to multiple projects (and one project to multiple environments)
- ✅ Link an already-existing environment to a new project instead of rejecting it
- ✅ Explicitly link an existing env with `condapm link <env>`
- ✅ Remove a project↔env association with `condapm unlink <env>`
- ✅ Open VS Code on a linked project with one command
- ✅ Filter project list by installed pip package (supports version constraints)
- ✅ Persistent configuration across sessions
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Show pip packages in each environment
- ✅ Works without an activated conda environment (auto-discovers conda from common install locations)
- ✅ Secret-scanning pre-commit hook (`detect-secrets`) blocks credentials from reaching git
- ✅ env_name restricted to `[A-Za-z0-9._-]` — shell metacharacters rejected at the domain layer
- ✅ VS Code subprocess uses `shell=False`; `.cmd` files invoked via explicit `cmd.exe /c`
- ✅ Corrupt `config.json` auto-recovers to safe defaults instead of crashing
- ✅ Relative paths in config silently skipped (path-traversal hardening)
- ✅ List pip packages for any named conda environment with `condapm list-packages`

## Architecture

The app uses a **layered architecture**:

```
CLI Layer (Typer + Rich)
    ↓
Application Layer (Use Cases)
    ↓
Infrastructure Layer (Adapters)
    ↓
Domain Layer (Entities)
```

Each layer has a single responsibility and can be tested independently.

## Tech Stack

- **CLI:** Typer (command-line interface)
- **Output:** Rich (pretty tables and colors)
- **Config:** JSON file (human-readable persistence)
- **Cross-platform:** pathlib + platformdirs
- **Testing:** pytest

## Directory Structure

```
conda-project-manager/
├── README.md                    # This file
├── pyproject.toml               # Dependencies and tool config
└── src/
    └── condapm/
        ├── __init__.py
        ├── cli.py              # CLI entry point (list-projects, create, open, link, unlink, list-packages, doctor, man)
        ├── domain/
        │   ├── project.py      # Project entity
        │   ├── environment.py  # CondaEnvironment entity
        │   ├── link.py         # ProjectEnvironmentLink entity
        │   ├── status.py       # ProjectStatus read model
        │   └── pip_package.py  # PipPackage value object
        ├── application/
        │   ├── __init__.py     # Public API re-exports
        │   ├── ports.py        # Adapter/store Protocols
        │   ├── exceptions.py   # EnvironmentNotFoundError, LinkNotFoundError
        │   ├── create.py       # CreateEnvironmentUseCase, EnvironmentAction
        │   ├── list.py         # ListProjectsUseCase
        │   ├── link.py         # LinkEnvironmentUseCase
        │   ├── unlink.py       # UnlinkEnvironmentUseCase
        │   ├── check.py        # CheckLinksUseCase, BrokenLink
        │   └── packages.py     # ListPackagesUseCase
        ├── infrastructure/
        │   ├── config_store.py # JSON persistence (flat links list)
        │   ├── conda_adapter.py# subprocess → conda
        │   ├── pip_adapter.py  # subprocess → pip
        │   └── vscode_adapter.py # subprocess → VS Code CLI
        └── ui/
            ├── formatters.py   # Rich table output
            └── manual.py       # man page definitions and renderer
```

## Installation

Install with [pipx](https://pipx.pypa.io) to make `condapm` available globally from any terminal:

```bash
pipx install -e "C:\Users\jorge.lago\Documents\Garrigues\Cloned_Projects\formacion\lab\condapm"
```

The `-e` flag installs in editable mode — changes to the source are reflected immediately without reinstalling.

After installation, `condapm` is on your PATH and works from any terminal, including plain PowerShell (no conda environment needs to be activated).

```bash
condapm list-projects
condapm list-projects --filter-pip fastapi
condapm create my-env --python 3.13
condapm link my-env
condapm unlink my-env
condapm open my-env
condapm list-packages my-env
condapm doctor
condapm man [COMMAND]
```
