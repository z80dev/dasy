from pathlib import Path
import warnings

import pytest

from dasy.compiler import compile_file as compile_dasy_file
from dasy.tools.dasy2vyper import emit_module_vyper
from dasy.parser.parse import parse_src
from vyper.compiler.input_bundle import FileInput
from vyper.compiler.phases import CompilerData as VyperCompilerData
from vyper.compiler.settings import Settings
from vyper import warnings as vy_warnings


EXAMPLES = sorted(
    Path(__file__).resolve().parent.parent.joinpath("examples").glob("*.dasy")
)


def _vyper_warnings_only(records):
    """Filter to Vyper warning categories only."""
    vy_types = (vy_warnings.VyperWarning, vy_warnings.Deprecation)
    return [w for w in records if isinstance(getattr(w, "message", None), vy_types)]


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_no_vyper_warnings_dasy_compile(path: Path):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        data = compile_dasy_file(str(path))
        _ = data.bytecode  # trigger Vyper compilation
    vy_w = _vyper_warnings_only(w)
    assert not vy_w, f"Vyper warnings on {path.name}:\n" + "\n".join(
        f"  {r.category.__name__}: {r.message}" for r in vy_w
    )


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_no_vyper_warnings_generated_vyper(path: Path):
    src = path.read_text()
    mod, _ = parse_src(src, filepath=str(path))
    vy_src = emit_module_vyper(mod)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        p = Path("test.vy")
        fi = FileInput(contents=vy_src, source_id=0, path=p, resolved_path=p)
        cd = VyperCompilerData(fi, settings=Settings())
        _ = cd.bytecode
    vy_w = _vyper_warnings_only(w)
    assert (
        not vy_w
    ), f"Vyper warnings on generated Vyper for {path.name}:\n" + "\n".join(
        f"  {r.category.__name__}: {r.message}" for r in vy_w
    )
