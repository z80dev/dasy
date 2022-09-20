from hy import models
from dasy import parser
from vyper.ast.nodes import BinOp, Compare, UnaryOp, BoolOp
from .utils import next_nodeid

BIN_FUNCS = ["+", "-", "/", "*", "**", "%"]
COMP_FUNCS = ["<", "<=", ">", ">=", "==", "!=", "in", "notin"]
UNARY_OPS = ["not"]
BOOL_OPS = ["and", "or"]


def is_op(cmd_str):
    return cmd_str in BIN_FUNCS + COMP_FUNCS + UNARY_OPS + BOOL_OPS


def parse_op(expr, alias=None):
    cmd_str = alias or str(expr[0])
    if cmd_str in BIN_FUNCS:
        return parse_binop(expr)
    if cmd_str in COMP_FUNCS:
        return parse_comparison(expr)
    if cmd_str in UNARY_OPS:
        return parse_unary(expr)
    if cmd_str in BOOL_OPS:
        return parse_boolop(expr)


def chain_comps(expr):
    new_node = models.Expression()
    new_expr = [models.Symbol("and")]
    for vals in zip(expr[1:], expr[2:]):
        new_expr.append(models.Expression((expr[0], vals[0], vals[1])))
    new_node += tuple(new_expr)
    return new_node


def parse_comparison(comp_tree):
    if (
        len(comp_tree[1:]) > 2
    ):  # comparing more than 2 things; chain comps for (< 2 3 4 )
        return parser.parse_node(chain_comps(comp_tree))
    left = parser.parse_node(comp_tree[1])
    right = parser.parse_node(comp_tree[2])
    op = parser.parse_node(comp_tree[0])
    return Compare(
        left=left,
        ops=[op],
        comparators=[right],
        node_id=next_nodeid(),
        ast_type="Compare",
    )


def parse_unary(expr):
    operand = parser.parse_node(expr[1])
    op = parser.parse_node(expr[0])
    return UnaryOp(operand=operand, op=op, node_id=next_nodeid(), ast_type="UnaryOp")


def parse_boolop(expr):
    op = parser.parse_node(expr[0])
    values = [parser.parse_node(e) for e in expr[1:]]
    return BoolOp(op=op, values=values, node_id=next_nodeid(), ast_type="BoolOp")


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
    if len(binop_tree) > 3:
        return parser.parse_node(chain_binops(binop_tree))
    left = parser.parse_node(binop_tree[1])
    right = parser.parse_node(binop_tree[2])
    op = parser.parse_node(binop_tree[0])
    return BinOp(left=left, right=right, op=op, node_id=next_nodeid(), ast_type="BinOp")
