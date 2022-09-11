from vyper.ast import nodes as vy_nodes
from hy import models
from dasy import parser
import dasy
from .core import process_body
from .utils import next_nodeid

def get_node(node_class, *args, **kwargs):
    return node_class(ast_type=node_class.__name__, node_id=next_nodeid(), *args, **kwargs)

def parse_continue(expr):
    return get_node(vy_nodes.Continue)

def parse_pass(expr):
    return get_node(vy_nodes.Pass)

def parse_break(expr):
    return get_node(vy_nodes.Break)

def parse_for(expr):
    # (for [x xs] (.append self/nums x))
    # (for [target iter] *body)
    target, iter_ = expr[1]
    target_node = parser.parse_node(target)
    iter_node = parser.parse_node(iter_)
    body_nodes = [parser.parse_node(b) for b in expr[2:]]
    body = process_body(body_nodes)
    for_node = get_node(vy_nodes.For, body=body, iter=iter_node, target=target_node)
    for_node._children.add(target_node)
    for_node._children.add(iter_node)
    iter_node._parent = for_node
    for n in body:
        for_node._children.add(n)
        n._parent = for_node
    return for_node

def parse_if(expr):
    if expr[1] == models.Keyword('else'):
        if expr[3] == models.Symbol('None'):
            return parser.parse_node(expr[2])
    body_nodes = [parser.parse_node(expr[2])]
    body = process_body(body_nodes)
    else_nodes = [parser.parse_node(expr[3])] if len(expr) == 4 else []
    else_ = process_body(else_nodes)
    test = parser.parse_node(expr[1])
    if_node = get_node(vy_nodes.If, test=test, body=body, orelse=else_)
    for n in body + else_ + [test]:
        if_node._children.add(n)
        n._parent = if_node
    return if_node

def parse_assert(assert_tree):
    msg = parser.parse_node(assert_tree[2]) if len(assert_tree) > 2 else None
    test = parser.parse_node(assert_tree[1])
    assert_node = get_node(vy_nodes.Assert, test=test, msg=msg)
    for n in [msg, test]:
        if n is not None:
            assert_node._children.add(n)
            n._parent = assert_node
    return assert_node


def parse_setv(expr):
    targets = [parser.parse_node(expr[1])]
    value = parser.parse_node(expr[2])
    assign_node = get_node(vy_nodes.Assign, targets=targets, value=value)
    for n in targets + [value]:
        assign_node._children.add(n)
        n._parent = assign_node
    return assign_node

def parse_augassign(expr):
    # (augassign op target value)
    # (augassign + self/num 4)
    return get_node(vy_nodes.AugAssign, op=parser.parse_node(expr[1]), target=parser.parse_node(expr[2]), value=parser.parse_node(expr[3]))

def parse_return(return_tree):
    return get_node(vy_nodes.Return, value=parser.parse_node(return_tree[1]))

def parse_raise(raise_tree):
    return get_node(vy_nodes.Raise, exc=parser.parse_node(raise_tree[1]))

def parse_log(log_tree):
    return get_node(vy_nodes.Log, value=parser.parse_node(log_tree[1]))

def parse_assign(expr):
    return parse_setv(expr)
