from vyper.ast import Call, Expr
import vyper.ast

from dasy import parser


def parse_vyper(expr):
    # Use vyper.ast.parse_to_ast instead of phases.generate_ast
    ast = vyper.ast.parse_to_ast(str(expr[1]), source_id=0)
    return ast.body[0]


def wrap_calls(nodes):
    new_nodes = []
    for call_node in nodes:
        if isinstance(call_node, Call):
            expr_node = parser.build_node(Expr, value=call_node)
            new_nodes.append(expr_node)
        else:
            new_nodes.append(call_node)
    return new_nodes


def parse_splice(expr):
    return_val = wrap_calls([parser.parse_node_legacy(n) for n in expr[1:]])
    return return_val
