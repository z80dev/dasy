# Repository Guidelines

## Project Structure & Module Organization
- `dasy/`: Core package. Key areas: `compiler.py` (entry), `parser/` (AST, macros, output), `macro/` (syntax rules), `builtin/` (functions, macros).
- `examples/`: Reference Dasy contracts for manual testing.
- `tests/`: Pytest suite targeting compiler behavior and examples.
- `pyproject.toml`: Packaging, dev extras, pytest config; build backend is `hatchling`.
- Docs: `README.org`, `docs.org`, and project notes in the root.

## Build, Test, and Development Commands
- Setup (recommended): `uv sync --dev`
- Run CLI: `uv run dasy examples/hello_world.dasy`
- List formats: `uv run dasy --list-formats`
- Tests: `uv run pytest -q`
- Format (check): `uv run black . --check` (auto-fix: drop `--check`)
- Without uv: `pip install -e .[dev] && pytest -q`

## Coding Style & Naming Conventions
- Python: Black-formatted, 4-space indent, snake_case for modules/functions, CapWords for classes.
- Hy/Lisp: Prefer kebab-case for macro/function names in `.hy` where idiomatic; keep files within `dasy/parser` or `dasy/builtin`.
- Imports: standard library → third-party → local. Avoid circular imports (see `dasy.main`).
- Logging: configure in CLI; library code should not call `basicConfig`.

## Testing Guidelines
- Framework: `pytest`. EVM tests use `titanoboa` (import `boa`) and Vyper 0.4.3.
- Location/naming: place tests in `tests/`, name `test_*.py`.
- Run: `uv run pytest -q`. Keep warnings clean (warnings are errors by default).
- Add minimal, focused tests for new syntax or compiler behavior; prefer example-driven tests under `examples/` when helpful.

## Commit & Pull Request Guidelines
- Style: Conventional prefixes seen in history (e.g., `tests:`, `cli:`, `build:`, `docs:`, `parser:`, `feat:`). Example: `parser: fix include! path resolution`.
- Commits: small, focused; include rationale when touching compiler or parser.
- PRs: target `main`; include description, linked issues, before/after notes or CLI output; add/adjust tests; ensure `pytest` and `black` pass.

## Security & Configuration Tips
- Supported Python: 3.10–3.11. Vyper pinned to `0.4.3`.
- Determinism: pin EVM version when needed via `--evm-version cancun` or `(pragma :evm-version cancun)`.
- No network requirements to compile. Review macros carefully; they run at compile time.
