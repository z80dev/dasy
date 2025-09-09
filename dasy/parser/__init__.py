import hy
import os
from .parse import parse_src, parse_node
from .compat import parse_node_compat, parse_expr_compat
from . import output, builtins
from pathlib import Path
from .utils import next_node_id_maker, build_node, next_nodeid

# Expose compat versions for backwards compatibility
parse_node_legacy = parse_node_compat
parse_expr_legacy = parse_expr_compat


def reset_nodeid_counter():
    builtins.next_nodeid = next_node_id_maker()


def install_builtin_macros():
    from .context import ParseContext

    macro_file = Path(os.path.dirname(__file__)).parent / "builtin" / "macros.hy"
    with macro_file.open() as f:
        code = f.read()
        # Create a minimal context for parsing builtin macros
        context = ParseContext(source_path=str(macro_file), source_code=code)
        for expr in hy.read_many(code):
            parse_node(expr, context)


install_builtin_macros()
