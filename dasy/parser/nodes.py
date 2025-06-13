from vyper.ast import nodes as vy_nodes
from vyper.ast.nodes import (
    Break,
    Pass,
    Continue,
    Log,
    Raise,
    Return,
    AugAssign,
    Assert,
    ExtCall,
    StaticCall,
)
from hy import models
from dasy import parser
from .utils import process_body, build_node


def parse_for(expr):
    # (for [x xs] (.append self/nums x))
    # (for [target iter] *body)
    target, iter_ = expr[1]
    target_node = parser.parse_node_legacy(target)
    iter_node = parser.parse_node_legacy(iter_)
    body_nodes = [parser.parse_node_legacy(b) for b in expr[2:]]
    body = process_body(body_nodes)
    for_node = build_node(vy_nodes.For, body=body, iter=iter_node, target=target_node)
    return for_node


def parse_if(expr):
    # used for base case in cond expansion
    if expr[1] == models.Keyword("else"):
        if expr[3] == models.Symbol("None"):
            return parser.parse_node_legacy(expr[2])

    body_nodes = [parser.parse_node_legacy(expr[2])]
    body = process_body(body_nodes)
    else_nodes = [parser.parse_node_legacy(expr[3])] if len(expr) == 4 else []
    else_ = process_body(else_nodes)
    test = parser.parse_node_legacy(expr[1])

    # if-expressions always have:
    # - one node in body
    # - one node in else
    # - both nodes are ExprNodes
    # in theory we could also verify that both ExprNodes are of the same type
    # but the Vyper compiler will catch that anyway
    if (
        len(body) == 1
        and len(else_) == 1
        and isinstance(body[0], vy_nodes.ExprNode)
        and isinstance(else_[0], vy_nodes.ExprNode)
    ):
        body = body[0]
        else_ = else_[0]
        if_node = build_node(vy_nodes.IfExp, test=test, body=body, orelse=else_)
    else:
        if_node = build_node(vy_nodes.If, test=test, body=body, orelse=else_)
    return if_node


def parse_assign(expr):
    # needs some slight massaging due to the way targets/target is treated
    # the Assign class has a target slot, but it uses the first value in the
    # targets arg to fill it instead of using the target kwarg
    args = [parser.parse_node_legacy(arg) for arg in expr[1:]]
    return build_node(vy_nodes.Assign, *args, targets=[args[0]])


def parse_expr(expr, nodes):
    return [parser.parse_node_legacy(node) for node in expr[1 : nodes + 1]]


handlers = {
    node_type.__name__.lower(): lambda expr, node_type=node_type: build_node(
        node_type, *parse_expr(expr, 2)
    )
    for node_type in [
        Break,
        Pass,
        Continue,
        Log,
        Raise,
        Return,
        AugAssign,
        Assert,
    ]
}


def parse_extcall(expr):
    # (extcall contract.method arg1 arg2 ...)
    # Build a Call node from the arguments
    if len(expr) < 2:
        raise ValueError("extcall requires at least a function call")
    
    # Parse the call expression
    call_expr = models.Expression(expr[1:])
    call_node = parser.parse_node_legacy(call_expr)
    
    # Wrap it in an ExtCall node
    return build_node(ExtCall, value=call_node)


def parse_staticcall(expr):
    # (staticcall contract.method arg1 arg2 ...)
    # Build a Call node from the arguments
    if len(expr) < 2:
        raise ValueError("staticcall requires at least a function call")
    
    # Parse the call expression
    call_expr = models.Expression(expr[1:])
    call_node = parser.parse_node_legacy(call_expr)
    
    # Wrap it in a StaticCall node
    return build_node(StaticCall, value=call_node)
