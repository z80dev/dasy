import hy
import os
from .parse import parse_src, parse_node
from . import output, builtins
from pathlib import Path
from .utils import next_node_id_maker, build_node, next_nodeid


def reset_nodeid_counter():
    builtins.next_nodeid = next_node_id_maker()


def install_builtin_macros():
    macro_file = Path(os.path.dirname(__file__)).parent / "builtin" / "macros.hy"
    with macro_file.open() as f:
        code = f.read()
        for expr in hy.read_many(code):
            parse_node(expr)


install_builtin_macros()
