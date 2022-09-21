from vyper.compiler.phases import CompilerData
from vyper.compiler.output import build_abi_output
from dasy.parser import parse_src


def compile(src: str, include_abi=True) -> CompilerData:
    ast = parse_src(src)
    data = CompilerData(
        "",
        ast.name,
        None,
        source_id=0,
    )
    data.vyper_module = ast
    if include_abi:
        data.__dict__["abi"] = build_abi_output(data)
    return data
