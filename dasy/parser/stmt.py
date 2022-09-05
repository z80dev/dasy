from dasy import parser
from vyper.ast.nodes import Assert, If, Assign, Raise, Return, AugAssign

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

def parse_augassign(expr):
    # (augassign op target value)
    # (augassign + self/num 4)
    return AugAssign(ast_type='Assign', node_id=next_nodeid(), op=parser.parse_node(expr[1]), target=parser.parse_node(expr[2]), value=parser.parse_node(expr[3]))

def parse_return(return_tree):
    return Return(value=parser.parse_node(return_tree[1]), ast_type='Return', node_id=next_nodeid())

def parse_assert(assert_tree):
    return Assert(ast_type='Assert', node_id=next_nodeid(), test=parser.parse_node(assert_tree[1]), msg=parser.parse_node(assert_tree[2]))

def parse_raise(raise_tree):
    return Raise(ast_type='Raise', node_id=next_nodeid(), exc=parser.parse_node(raise_tree[1]))
