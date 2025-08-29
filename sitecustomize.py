"""
sitecustomize: test-time shims and environment tweaks.

This module is auto-imported by Python if present on sys.path. We use it to
backfill a compatibility function expected by titanoboa/boa against newer
Vyper versions.

Specifically, older boa expects `vyper.cli.vyper_compile.get_interface_codes`,
which no longer exists in Vyper 0.4.x. We provide a minimal stub that returns
an empty interface map for each contract, which is sufficient for our tests
since they do not rely on Vyper import resolution.
"""
from __future__ import annotations

from pathlib import Path


def _install_get_interface_codes_stub() -> None:
    try:
        import vyper.cli.vyper_compile as vc  # type: ignore
    except Exception:
        return

    if hasattr(vc, "get_interface_codes"):
        return

    def get_interface_codes(_base_path: Path, contracts: dict[str, str]) -> dict[str, dict]:
        # Return an empty interface dict per contract key
        return {name: {} for name in contracts.keys()}

    # attach stub
    setattr(vc, "get_interface_codes", get_interface_codes)


_install_get_interface_codes_stub()


def _backfill_vyper_ast_utils() -> None:
    try:
        import vyper.ast as vy_ast  # type: ignore
        import vyper.ast.utils as vu  # type: ignore
    except Exception:
        return

    if not hasattr(vu, "parse_to_ast") and hasattr(vy_ast, "parse_to_ast"):
        setattr(vu, "parse_to_ast", getattr(vy_ast, "parse_to_ast"))


_backfill_vyper_ast_utils()


def _backfill_generate_ir_for_function() -> None:
    try:
        # function_definitions module contains codegen entry points
        import vyper.codegen.function_definitions as fd  # type: ignore
        from vyper.codegen.function_definitions.common import (  # type: ignore
            ExternalFuncIR,
            InternalFuncIR,
        )
    except Exception:
        return

    if hasattr(fd, "generate_ir_for_function"):
        return

    # define a compatibility wrapper matching older boa expectations
    def generate_ir_for_function(code, compilation_target, is_ctor_context=False):
        # try external first
        if hasattr(fd, "generate_ir_for_external_function"):
            try:
                res = fd.generate_ir_for_external_function(code, compilation_target)
                if isinstance(res, ExternalFuncIR):
                    return res
            except Exception:
                pass
        # fall back to internal
        if hasattr(fd, "generate_ir_for_internal_function"):
            return fd.generate_ir_for_internal_function(code, compilation_target, bool(is_ctor_context))
        raise RuntimeError("vyper.codegen.function_definitions has no suitable IR generators")

    setattr(fd, "generate_ir_for_function", generate_ir_for_function)


_backfill_generate_ir_for_function()


def _alias_global_context_module() -> None:
    try:
        import sys
        import importlib
        # If vyper.codegen.global_context is missing, alias to vyper.codegen.context
        spec = importlib.util.find_spec('vyper.codegen.global_context')
        if spec is None:
            ctx = importlib.import_module('vyper.codegen.context')
            # Provide expected GlobalContext symbol
            if not hasattr(ctx, 'GlobalContext') and hasattr(ctx, 'Context'):
                setattr(ctx, 'GlobalContext', getattr(ctx, 'Context'))
            sys.modules['vyper.codegen.global_context'] = ctx
    except Exception:
        return


_alias_global_context_module()


def _backfill_codegen_core_getpos() -> None:
    try:
        import vyper.codegen.core as core  # type: ignore
        if hasattr(core, 'getpos'):
            return
        # minimal getpos compatible with boa's usage (lineno-based mapping)
        def getpos(node):
            lineno = getattr(node, 'lineno', None)
            end_lineno = getattr(node, 'end_lineno', lineno)
            col = getattr(node, 'col_offset', 0)
            end_col = getattr(node, 'end_col_offset', 0)
            # Return a tuple where index 0 is lineno, matching boa expectations
            return (lineno, col, end_lineno, end_col)

        setattr(core, 'getpos', getpos)
    except Exception:
        return


_backfill_codegen_core_getpos()
