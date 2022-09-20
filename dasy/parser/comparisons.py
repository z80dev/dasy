from hy import models
from dasy import parser
from .utils import next_nodeid
import vyper.ast.nodes as vy_nodes

COMP_FUNCS = ["<", "<=", ">", ">=", "==", "!="]


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
    return vy_nodes.Compare(
        left=left,
        ops=[op],
        comparators=[right],
        node_id=next_nodeid(),
        ast_type="Compare",
    )
