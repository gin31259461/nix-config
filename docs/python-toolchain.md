# Python toolchain

Python in this repository is an implementation language for deployment adapters
and repository tooling. The runtime remains Nix-owned.

## Dependency authority

`pyproject.toml` declares Python requirements and `uv.lock` is the resolved Python
dependency graph. uv2nix projects that graph into Nix derivations. `flake.lock`
continues to pin Nixpkgs, Home Manager and the uv2nix toolchain itself.

The intended flow is:

```text
pyproject.toml -> uv lock -> uv.lock -> uv2nix -> Nix Python closure
```

Production and CI must not depend on a mutable `.venv`, an Arch system Python, or
a Python downloaded by uv. The development shell therefore sets:

```text
UV_NO_SYNC=1
UV_PYTHON=<Nix Python 3.12>
UV_PYTHON_DOWNLOADS=never
```

Use `uv add`, `uv remove` and `uv lock` to change the dependency graph. Use
`nix develop`, `nix build`, `nix run` and `nix flake check` to execute repository
code. Do not make `uv sync`, `uv run` or `uv python install` part of deployment.

## Runtime boundary

`lib/python-runtime.nix` is the single projection from `uv.lock` to the Nix Python
runtime. Home Manager tooling, Arch adapters and repository checks receive that
runtime instead of constructing ad-hoc `python3.withPackages` environments.

Python is currently a virtual project (`tool.uv.package = false`). If the Arch
coordinator becomes a standalone importable application with a real `src/`
package and CLI entry point, convert it to a packaged project deliberately rather
than mixing packaging concerns into the current script-oriented layout.

## Validation

Ruff reads its policy from `pyproject.toml`. Pyright is enabled incrementally at
the serialized privileged boundary first. ShellCheck covers the remaining shell
orchestration while it is migrated in bounded steps.

After dependency changes, regenerate `uv.lock` and run:

```bash
just check
```
