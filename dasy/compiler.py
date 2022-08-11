from vyper.compiler.phases import CompilerData
from dasy.parser import parse_src

def compile(src: str) -> CompilerData:
    ast = parse_src(src)
    data = CompilerData("", ast.name, None, source_id=0, )
    data.vyper_module = ast
    return data
