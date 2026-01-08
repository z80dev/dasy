"""Tests that run all behavioral tests against different compilation pipelines.

This module runs the same tests from test_dasy.py through:
1. dasy2vyper: Dasy -> Vyper source -> compiled with Vyper
2. roundtrip: Dasy -> Vyper source -> Dasy source -> compiled with Dasy

This ensures that the conversion tools produce functionally equivalent code.
"""

import pytest

# Import the original Dasy tests module
import tests.test_dasy as td

from dasy.tools.dasy2vyper import emit_module_vyper
from dasy.tools.vyper2dasy import emit_module_dasy
from dasy.parser.parse import parse_src
from vyper.compiler.input_bundle import FileInput
from dasy.compiler import CompilerData as DasyCompilerData
from vyper.compiler.settings import Settings
from pathlib import Path
from boa.contracts.vyper.vyper_contract import VyperContract
import vyper.ast as vast
import dasy


# ============================================================================
# Compilation helpers for dasy2vyper mode
# ============================================================================


def _compile_vyper_source(vy_src: str, *args) -> VyperContract:
    fi = FileInput(
        contents=vy_src,
        source_id=0,
        path=Path("test.vy"),
        resolved_path=Path("test.vy"),
    )
    cd = DasyCompilerData(fi, settings=Settings())
    return VyperContract(cd, *args)


def _compile_src_vyper(src: str, *args) -> VyperContract:
    mod, _ = parse_src(src)
    vy_src = emit_module_vyper(mod)
    return _compile_vyper_source(vy_src, *args)


def _compile_file_vyper(filename: str, *args) -> VyperContract:
    base = Path(__file__).resolve().parent.parent
    path = (base / filename).resolve()
    src = path.read_text()
    mod, _ = parse_src(src, filepath=str(path))
    vy_src = emit_module_vyper(mod)
    return _compile_vyper_source(vy_src, *args)


# ============================================================================
# Compilation helpers for roundtrip mode (Dasy -> Vyper -> Dasy)
# ============================================================================


def _compile_src_roundtrip(src: str, *args) -> VyperContract:
    """Compile Dasy source via full roundtrip: Dasy -> Vyper -> Dasy."""
    # Dasy -> Vyper AST -> Vyper source
    mod, _ = parse_src(src)
    vy_src = emit_module_vyper(mod)
    # Vyper source -> Vyper AST -> Dasy source
    vy_mod = vast.parse_to_ast(vy_src, source_id=0)
    dasy_src = emit_module_dasy(vy_mod)
    # Compile the roundtripped Dasy
    ast = dasy.compile(dasy_src, include_abi=True)
    return VyperContract(ast, *args)


def _compile_file_roundtrip(filename: str, *args) -> VyperContract:
    """Compile Dasy file via full roundtrip: Dasy -> Vyper -> Dasy."""
    base = Path(__file__).resolve().parent.parent
    path = (base / filename).resolve()
    src = path.read_text()
    # Dasy -> Vyper AST -> Vyper source
    mod, _ = parse_src(src, filepath=str(path))
    vy_src = emit_module_vyper(mod)
    # Vyper source -> Vyper AST -> Dasy source
    vy_mod = vast.parse_to_ast(vy_src, source_id=0)
    dasy_src = emit_module_dasy(vy_mod)
    # Compile the roundtripped Dasy
    ast = dasy.compile(dasy_src, include_abi=True)
    return VyperContract(ast, *args)


# ============================================================================
# Parametrized tests
# ============================================================================

# Collect all test functions from test_dasy
_test_functions = [
    getattr(td, name)
    for name in dir(td)
    if name.startswith("test_") and callable(getattr(td, name))
]
_test_ids = [name for name in dir(td) if name.startswith("test_")]


@pytest.mark.parametrize("test_fn", _test_functions, ids=_test_ids)
def test_all_against_generated_vyper(monkeypatch, test_fn):
    """Run all tests with contracts compiled via dasy2vyper -> Vyper."""
    # Patch the compile helpers used by the tests to route through generated Vyper
    monkeypatch.setattr(td, "compile_src", _compile_src_vyper)
    monkeypatch.setattr(td, "compile", _compile_file_vyper)
    # Run the original test function
    test_fn()


@pytest.mark.parametrize("test_fn", _test_functions, ids=_test_ids)
def test_all_against_roundtrip(monkeypatch, test_fn):
    """Run all tests with contracts compiled via Dasy -> Vyper -> Dasy roundtrip."""
    # Patch the compile helpers used by the tests to route through roundtrip
    monkeypatch.setattr(td, "compile_src", _compile_src_roundtrip)
    monkeypatch.setattr(td, "compile", _compile_file_roundtrip)
    # Run the original test function
    test_fn()
