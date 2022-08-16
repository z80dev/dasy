from hy import models
from dasy import parser
from vyper.ast.nodes import BinOp
from .utils import next_nodeid

BIN_FUNCS = ['+', '-', '/', '*']

def chain_binops(expr):
    if len(expr) == 3:
        return expr
    else:
        new_node = models.Expression()
        tmp_expr = tuple([expr[0], *expr[2:]])
        tmp_node = models.Expression()
        tmp_node += tmp_expr
        subtree = chain_binops(tmp_node)
        new_node += tuple([expr[0], expr[1], subtree])
        return new_node


def parse_binop(binop_tree):
    match str(binop_tree[0]):
        case '+' | '-' | '*' | '/':
            if len(binop_tree) > 3:
                return parser.parse_node(chain_binops(binop_tree))
            left = parser.parse_node(binop_tree[1])
            right = parser.parse_node(binop_tree[2])
            op = parser.parse_node(binop_tree[0])
            return BinOp(left=left, right=right, op=op, node_id=next_nodeid(), ast_type='BinOp')
