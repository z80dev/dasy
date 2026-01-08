from .parse import parse_src, parse_node
from .compat import parse_node_compat, parse_expr_compat
from . import output, builtins
from .utils import next_node_id_maker, build_node, next_nodeid

# Expose compat versions for backwards compatibility
parse_node_legacy = parse_node_compat
parse_expr_legacy = parse_expr_compat


def reset_nodeid_counter():
    builtins.next_nodeid = next_node_id_maker()
