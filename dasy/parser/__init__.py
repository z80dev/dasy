import hy
import os
from .parse import parse_src, parse_node
from .utils import next_node_id_maker
from . import utils, output
from pathlib import Path


def reset_nodeid_counter():
    utils.next_nodeid = next_node_id_maker()


def install_builtin_macros():
    macro_file = Path(os.path.dirname(__file__)).parent / "builtin" / "macros.hy"
    with macro_file.open() as f:
        code = f.read()
        for expr in hy.read_many(code):
            parse_node(expr)


install_builtin_macros()
