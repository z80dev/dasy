from dasy import parser
from vyper.ast.nodes import If, Assign, Return

from dasy.parser.core import process_body
from .utils import next_nodeid

def parse_if(expr):
    body_nodes = [parser.parse_node(expr[2])]
    body = process_body(body_nodes)
    else_nodes = [parser.parse_node(expr[3])] if len(expr) == 4 else []
    else_ = process_body(else_nodes)
    return If(ast_type='If', node_id=next_nodeid(), test=parser.parse_node(expr[1]), body=body, orelse=else_)

def parse_setv(expr):
    return Assign(ast_type='Assign', node_id=next_nodeid(), targets=[parser.parse_node(expr[1])], value=parser.parse_node(expr[2]))

def parse_return(return_tree):
    return Return(value=parser.parse_node(return_tree[1]), ast_type='Return', node_id=next_nodeid())
