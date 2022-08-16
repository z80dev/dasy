from dasy import parser
from vyper.ast.nodes import If, Assign, Return
from .utils import next_nodeid

def parse_if(expr):
    return If(ast_type='If', node_id=next_nodeid(), test=parser.parse_node(expr[1]), body=[parser.parse_node(expr[2])], orelse=[parser.parse_node(expr[3])])

def parse_assignment(expr):
    match expr[1:]:
        case [target, value]:
            return Assign(ast_type='Call', node_id=next_nodeid(), targets=[parser.parse_node(target)], value=parser.parse_node(value))

def parse_return(return_tree):
    val = return_tree[1]
    value_node = parser.parse_node(val)
    return_node = Return(value=value_node, ast_type='Return', node_id=next_nodeid())
    return return_node
