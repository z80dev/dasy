from typing import List, Union
from hy import models
from dasy import parser
import vyper.ast.nodes as vy_nodes
from hy.models import Expression, Symbol

COMP_FUNCS = ["<", "<=", ">", ">=", "==", "!="]


def chain_comps(chain_expr: Expression) -> Expression:
    """
    Creates a new expression chaining comparisons.
    """
    new_node = models.Expression()
    new_expr: List[Union[Symbol, Expression]] = [models.Symbol("and")]
    for vals in zip(chain_expr[1:], chain_expr[2:]):
        new_expr.append(models.Expression((chain_expr[0], vals[0], vals[1])))
    new_node += tuple(new_expr)
    return new_node


def parse_comparison(comparison_expr: Expression) -> vy_nodes.Compare:
    """
    Parses a comparison expression, chaining comparisons if necessary.
    """
    assert (
        str(comparison_expr[0]) in COMP_FUNCS
    ), f"Invalid comparison operator {comparison_expr[0]}"

    # Always apply chain comps for consistency
    chained_expr = chain_comps(comparison_expr)
    left = parser.parse_node(chained_expr[1])
    right = parser.parse_node(chained_expr[2])
    op = parser.parse_node(chained_expr[0])
    return parser.build_node(vy_nodes.Compare, left=left, ops=[op], comparators=[right])
