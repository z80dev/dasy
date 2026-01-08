"""Shared pytest fixtures for Dasy tests.

Provides compilation modes for testing contracts through different pipelines:
- dasy: Direct Dasy compilation (default)
- dasy2vyper: Dasy -> Vyper -> compile with Vyper
- roundtrip: Dasy -> Vyper -> Dasy -> compile with Dasy
"""

import pytest
from pathlib import Path
from boa.contracts.vyper.vyper_contract import VyperContract
from vyper.compiler.input_bundle import FileInput
from vyper.compiler.settings import Settings

import dasy
from dasy.parser.parse import parse_src
from dasy.tools.dasy2vyper import emit_module_vyper
from dasy.tools.vyper2dasy import emit_module_dasy
from dasy.compiler import CompilerData as DasyCompilerData
import vyper.ast as vast


# ============================================================================
# Compilation helpers for each mode
# ============================================================================


def _compile_dasy_src(src: str, *args) -> VyperContract:
    """Compile Dasy source directly."""
    ast = dasy.compile(src, include_abi=True)
    return VyperContract(ast, *args)


def _compile_dasy_file(filename: str, *args) -> VyperContract:
    """Compile Dasy file directly."""
    base = Path(__file__).resolve().parent.parent
    path = (base / filename).resolve()
    data = dasy.compile_file(str(path))
    return VyperContract(data, *args)


def _compile_vyper_source(vy_src: str, *args) -> VyperContract:
    """Compile Vyper source code."""
    fi = FileInput(
        contents=vy_src,
        source_id=0,
        path=Path("test.vy"),
        resolved_path=Path("test.vy"),
    )
    cd = DasyCompilerData(fi, settings=Settings())
    return VyperContract(cd, *args)


def _compile_dasy2vyper_src(src: str, *args) -> VyperContract:
    """Compile Dasy source via dasy2vyper -> Vyper."""
    mod, _ = parse_src(src)
    vy_src = emit_module_vyper(mod)
    return _compile_vyper_source(vy_src, *args)


def _compile_dasy2vyper_file(filename: str, *args) -> VyperContract:
    """Compile Dasy file via dasy2vyper -> Vyper."""
    base = Path(__file__).resolve().parent.parent
    path = (base / filename).resolve()
    src = path.read_text()
    mod, _ = parse_src(src, filepath=str(path))
    vy_src = emit_module_vyper(mod)
    return _compile_vyper_source(vy_src, *args)


def _compile_roundtrip_src(src: str, *args) -> VyperContract:
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


def _compile_roundtrip_file(filename: str, *args) -> VyperContract:
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
# Compilation mode configurations
# ============================================================================

COMPILATION_MODES = {
    "dasy": {
        "compile_src": _compile_dasy_src,
        "compile_file": _compile_dasy_file,
        "description": "Direct Dasy compilation",
    },
    "dasy2vyper": {
        "compile_src": _compile_dasy2vyper_src,
        "compile_file": _compile_dasy2vyper_file,
        "description": "Dasy -> dasy2vyper -> Vyper compilation",
    },
    "roundtrip": {
        "compile_src": _compile_roundtrip_src,
        "compile_file": _compile_roundtrip_file,
        "description": "Dasy -> Vyper -> Dasy roundtrip compilation",
    },
}


@pytest.fixture(params=list(COMPILATION_MODES.keys()))
def compilation_mode(request):
    """Fixture that provides compilation mode name."""
    return request.param


@pytest.fixture
def compile_src(compilation_mode):
    """Fixture that provides compile_src function for current mode."""
    return COMPILATION_MODES[compilation_mode]["compile_src"]


@pytest.fixture
def compile_file(compilation_mode):
    """Fixture that provides compile (file) function for current mode."""
    return COMPILATION_MODES[compilation_mode]["compile_file"]
