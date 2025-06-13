import hy
from hy import read, read_many
from dasy.compiler import compile, compile_file
from dasy.main import main
from dasy.parser.output import get_external_interface
from .parser import parse
from .parser.parse import parse_src, parse_node
from .parser.compat import parse_node_compat, parse_expr_compat

# Provide backwards-compatible versions at the module level
parse_node_legacy = parse_node_compat
parse_expr_legacy = parse_expr_compat

__version__ = "0.1.29"
