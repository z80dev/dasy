from dasy import parser
from vyper.ast.nodes import If, Assign, Return
from .utils import next_nodeid

def parse_if(expr):
    return If(ast_type='If', node_id=next_nodeid(), test=parser.parse_node(expr[1]), body=[parser.parse_node(expr[2])], orelse=[parser.parse_node(expr[3])])

def parse_setv(expr):
    return Assign(ast_type='Assign', node_id=next_nodeid(), targets=[parser.parse_node(expr[1])], value=parser.parse_node(expr[2]))

def parse_return(return_tree):
    return Return(value=parser.parse_node(return_tree[1]), ast_type='Return', node_id=next_nodeid())
