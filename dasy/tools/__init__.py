"""Command-line conversion tools for Dasy <-> Vyper.

This package provides two entrypoints:
- dasy2vyper: Convert Dasy source to approximated Vyper source.
- vyper2dasy: Convert Vyper source to approximated Dasy source.

The conversion is best-effort and currently supports common constructs
used in this repository (state vars, basic expressions, returns, assigns,
ifs, simple loops, calls). For unsupported nodes, the converters insert
TODO comments or wrap raw Vyper lines using the `(vyper "...")` macro
to preserve semantics.
"""
