# Dasy Improvement Plan (non-CI)

This document tracks the planned improvements requested, excluding CI changes. Progress is updated as changes land.

Status legend: [x] done, [~] in progress, [ ] pending

## Packaging & Release

- [x] Remove `argparse` from runtime deps (stdlib)
- [x] Change entry point to `dasy.main:main`
- [x] Add `readme`, `classifiers`, `urls`, `keywords` to `pyproject.toml`
- [x] Add optional dev extras: `ruff`, `mypy`, `pytest-cov` (no CI)
- [ ] Note: License metadata requires maintainer decision (left pending)

## CLI & UX

- [x] Add `--list-formats` and `--version`
- [x] Add `--evm-version` passthrough to compiler settings
- [x] Add `--verbose/--quiet` logging controls
- [x] Improve error messages for bad `-f/--format`
- [ ] Optional: `--expand` (print expanded forms) — deferred unless requested

## Logging & Errors

- [x] Remove global `basicConfig(level=DEBUG)` default; default to WARNING
- [x] Keep detailed debug available via `--verbose`

## Docs & Examples

- [x] Fix `dyn-arr` → `dyn-array` in `README.org`

## Validation

- [x] Run tests to ensure nothing breaks

---

### Changelog of this plan

- v1: Created plan and outlined tasks
