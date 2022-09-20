import hy
import os
from .parse import parse_src, parse_node
from pathlib import Path


def install_builtin_macros():
    macro_file = Path(os.path.dirname(__file__)).parent / "builtin" / "macros.hy"
    with macro_file.open() as f:
        code = f.read()
        for expr in hy.read_many(code):
            parse_node(expr)


install_builtin_macros()
