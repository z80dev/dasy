from vyper.ast import nodes as vy_nodes
from vyper.ast.nodes import (
    Break,
    Pass,
    Continue,
    Log,
    Raise,
    Return,
    AugAssign,
    Assign,
    Assert,
    AnnAssign,
    Index,
)
from hy import models
from dasy import parser
import dasy
from .core import parse_annassign, process_body
from .utils import next_nodeid

handlers = {}


def get_node(node_class, *args, **kwargs):
    args_dict = kwargs
    if len(args) != 0:
        for slot, value in zip(node_class.__slots__, args):
            args_dict[slot] = value
        for slot in node_class.__slots__[len(args) :]:
            args_dict[slot] = None
        args = []
    new_node = node_class(
        ast_type=node_class.__name__, node_id=next_nodeid(), *args, **args_dict
    )
    set_parent_children(new_node, args_dict.values())
    return new_node


def set_parent_children(parent, children):
    for n in children:
        if n is not None:
            if isinstance(n, list):
                set_parent_children(parent, n)
            else:
                parent._children.add(n)
                n._parent = parent


for node_type in [Break, Pass, Continue, Log, Raise, Return, AugAssign, Assert, Index]:
    k = node_type.__name__.lower()
    handlers[k] = lambda expr, node_type=node_type: get_node(
        node_type, *[parser.parse_node(arg) for arg in expr[1:]]
    )


def parse_for(expr):
    # (for [x xs] (.append self/nums x))
    # (for [target iter] *body)
    target, iter_ = expr[1]
    target_node = parser.parse_node(target)
    iter_node = parser.parse_node(iter_)
    body_nodes = [parser.parse_node(b) for b in expr[2:]]
    body = process_body(body_nodes)
    for_node = get_node(vy_nodes.For, body=body, iter=iter_node, target=target_node)
    set_parent_children(for_node, body + [target_node, iter_node])
    return for_node


def parse_if(expr):
    # used for base case in cond expansion
    if expr[1] == models.Keyword("else"):
        if expr[3] == models.Symbol("None"):
            return parser.parse_node(expr[2])

    body_nodes = [parser.parse_node(expr[2])]
    body = process_body(body_nodes)
    else_nodes = [parser.parse_node(expr[3])] if len(expr) == 4 else []
    else_ = process_body(else_nodes)
    test = parser.parse_node(expr[1])
    if_node = get_node(vy_nodes.If, test=test, body=body, orelse=else_)
    set_parent_children(if_node, body + else_ + [test])
    return if_node


def parse_assign(expr):
    # needs some slight massaging due to the way targets/target is treated
    # the Assign class has a target slot, but it uses the first value in the
    # targets arg to fill it instead of using the target kwarg
    args = [parser.parse_node(arg) for arg in expr[1:]]
    return get_node(vy_nodes.Assign, *args, targets=[args[0]])
