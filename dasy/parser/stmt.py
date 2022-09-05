from dasy import parser
from vyper.ast.nodes import If, Assign, Return
from .utils import next_nodeid

def parse_if(expr):
    body_nodes = [parser.parse_node(expr[2])]
    body = []
    for n in body_nodes:
        if isinstance(n, list):
            for i_n in n:
                body.append(i_n)
        else:
            body.append(n)
    else_nodes = [parser.parse_node(expr[3])] if len(expr) == 4 else []
    else_ = []
    for n in else_nodes:
        if isinstance(n, list):
            for i_n in n:
                else_.append(i_n)
        else:
            else_.append(n)
    return If(ast_type='If', node_id=next_nodeid(), test=parser.parse_node(expr[1]), body=body, orelse=else_)

def parse_setv(expr):
    return Assign(ast_type='Assign', node_id=next_nodeid(), targets=[parser.parse_node(expr[1])], value=parser.parse_node(expr[2]))

def parse_return(return_tree):
    return Return(value=parser.parse_node(return_tree[1]), ast_type='Return', node_id=next_nodeid())
