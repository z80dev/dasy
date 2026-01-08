from vyper.ast import Call, Expr

from dasy import parser


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
