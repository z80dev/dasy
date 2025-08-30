# Dasy Improvement Plan (non-CI)

This document tracks the planned improvements requested, excluding CI changes. Progress is updated as changes land.

Status legend: [x] done, [~] in progress, [ ] pending

## Packaging & Release

- [ ] Remove `argparse` from runtime deps (stdlib)
- [ ] Change entry point to `dasy.main:main`
- [ ] Add `readme`, `classifiers`, `urls`, `keywords` to `pyproject.toml`
- [ ] Add optional dev extras: `ruff`, `mypy`, `pytest-cov` (no CI)
- [ ] Note: License metadata requires maintainer decision (left pending)

## CLI & UX

- [ ] Add `--list-formats` and `--version`
- [ ] Add `--evm-version` passthrough to compiler settings
- [ ] Add `--verbose/--quiet` logging controls
- [ ] Improve error messages for bad `-f/--format`
- [ ] Optional: `--expand` (print expanded forms) — deferred unless requested

## Logging & Errors

- [ ] Remove global `basicConfig(level=DEBUG)` default; default to WARNING
- [ ] Keep detailed debug available via `--verbose`

## Docs & Examples

- [ ] Fix `dyn-arr` → `dyn-array` in `README.org`

## Validation

- [ ] Run tests to ensure nothing breaks

---

### Changelog of this plan

- v1: Created plan and outlined tasks
