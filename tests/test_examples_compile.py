from pathlib import Path

import pytest

from dasy.compiler import compile_file as compile_dasy_file
from dasy.tools.dasy2vyper import emit_module_vyper
from dasy.parser.parse import parse_src
from vyper.compiler.input_bundle import FileInput
from dasy.compiler import CompilerData as DasyCompilerData
from vyper.compiler.settings import Settings


EXAMPLES = sorted(Path(__file__).resolve().parent.parent.joinpath("examples").glob("*.dasy"))


def _compile_vyper_source(vy_src: str):
    fi = FileInput(contents=vy_src, source_id=0, path=Path("test.vy"), resolved_path=Path("test.vy"))
    cd = DasyCompilerData(fi, settings=Settings())
    _ = cd.bytecode


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_compile_dasy(path: Path):
    data = compile_dasy_file(str(path))
    _ = data.bytecode


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_compile_generated_vyper(path: Path):
    src = path.read_text()
    mod, _ = parse_src(src, filepath=str(path))
    vy_src = emit_module_vyper(mod)
    _compile_vyper_source(vy_src)
