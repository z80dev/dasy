import types
import pytest

# Import the original Dasy tests module
import tests.test_dasy as td

from dasy.tools.dasy2vyper import emit_module_vyper
from dasy.parser.parse import parse_src
from vyper.compiler.input_bundle import FileInput
from dasy.compiler import CompilerData as DasyCompilerData
from vyper.compiler.settings import Settings
from pathlib import Path
from boa.contracts.vyper.vyper_contract import VyperContract


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


@pytest.mark.parametrize(
    "test_fn",
    [
        getattr(td, name)
        for name in dir(td)
        if name.startswith("test_") and callable(getattr(td, name))
    ],
    ids=[name for name in dir(td) if name.startswith("test_")],
)
def test_all_against_generated_vyper(monkeypatch, test_fn):
    # Patch the compile helpers used by the tests to route through generated Vyper
    monkeypatch.setattr(td, "compile_src", _compile_src_vyper)
    monkeypatch.setattr(td, "compile", _compile_file_vyper)
    # Run the original test function
    test_fn()
