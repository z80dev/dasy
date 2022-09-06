from ast import Expression

import dasy
import vyper.ast.nodes as vy_nodes
from hy import models

from .utils import has_return, next_nodeid, pairwise


def parse_attribute(expr):
    match expr[1:]:
        case [obj, attr]:
            value_node = dasy.parser.parse_node(obj)
            attr_node = vy_nodes.Attribute(ast_type='Attribute', node_id=next_nodeid(), attr=str(attr), value=value_node)
            attr_node._children.add(value_node)
            return attr_node

def parse_call(expr, wrap_expr=False):
    match expr:
        case (fn_name, *args):
            args_list = [dasy.parser.parse_node(arg) for arg in args]
            func_node = dasy.parser.parse_node(fn_name)
            call_node = vy_nodes.Call(func=func_node, args=args_list, keywords=[], ast_type='Call', node_id=next_nodeid())
            call_node._children.add(func_node)
            for a in args_list:
                call_node._children.add(a)
            if wrap_expr:
                expr_node = vy_nodes.Expr(ast_type='Expr', node_id=next_nodeid(), value=call_node)
                expr_node._children.add(call_node)
                return expr_node
            return call_node

def parse_for(expr):
    # (for [x xs] (.append self/nums x))
    # (for [target iter] *body)
    target, iter_ = expr[1]
    target_node = dasy.parser.parse_node(target)
    iter_node = dasy.parser.parse_node(iter_)
    body_nodes = [dasy.parser.parse_node(b) for b in expr[2:]]
    body = process_body(body_nodes)
    for_node = vy_nodes.For(ast_type='For', node_id=next_nodeid(), body=body, iter=iter_node, target=target_node)
    for_node._children.add(target_node)
    for_node._children.add(iter_node)
    for n in body:
        for_node._children.add(n)
    return for_node


def parse_tuple(tuple_tree):
    match tuple_tree:
        case models.Symbol(q), elements if str(q) == 'quote':
            elts = [dasy.parser.parse_node(e) for e in elements]
            tuple_node = vy_nodes.Tuple(elements=elts, node_id=next_nodeid(), ast_type='Tuple')
            return tuple_node
        case models.Symbol(q), *elements if str(q) == 'tuple':
            elts = [dasy.parser.parse_node(e) for e in elements]
            tuple_node = vy_nodes.Tuple(elements=elts, node_id=next_nodeid(), ast_type='Tuple')
            return tuple_node
        case _:
            raise Exception("Invalid tuple declaration; requires quoted list or tuple-fn ex: '(2 3 4)/(tuple 2 3 4)")

def parse_args_list(args_list) -> list[vy_nodes.arg]:
    if len(args_list) == 0:
        return []
    results = []
    current_type = args_list[0]
    assert isinstance(current_type, models.Keyword) or isinstance(current_type, models.Expression)
    # get annotation and name
    for arg in args_list[1:]:
        # check if we hit a new type
        if isinstance(arg, models.Keyword) or isinstance(arg, models.Expression):
            current_type = arg
            continue
        # get annotation and name
        if isinstance(current_type, models.Keyword):
            annotation_node = vy_nodes.Name(id=str(current_type.name), parent=None, node_id=next_nodeid(), ast_type='Name')
        elif isinstance(current_type, models.Expression):
            annotation_node = dasy.parse.parse_node(current_type)
        results.append(vy_nodes.arg(arg=str(arg), parent=None, annotation=annotation_node, node_id=next_nodeid()))
    return results

def process_body(body):
    # flatten list if necessary
    # wrap raw Call in Expr if needed
    new_body = []
    for f in body:
        if isinstance(f, list):
            for f2 in f:
                new_body.append(f2)
        elif isinstance(f, vy_nodes.List):
            for f2 in f.elements:
                if isinstance(f2, vy_nodes.Call):
                    expr_node = vy_nodes.Expr(ast_type='Expr', node_id=next_nodeid(), value=f2)
                    new_body.append(expr_node)
                else:
                    new_body.append(f2)
        elif isinstance(f, vy_nodes.Call):
            expr_node = vy_nodes.Expr(ast_type='Expr', node_id=next_nodeid(), value=f)
            new_body.append(expr_node)
        else:
            new_body.append(f)
    return new_body


def parse_defn(fn_tree):
    fn_node_id = next_nodeid()
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol('defn')
    rets = None
    name = str(fn_tree[1])
    args = None
    decorators = []

    if str(fn_tree[1]) == "__init__":
        args_node, decs, *body = fn_tree[2:]
        args_list = parse_args_list(args_node)
        args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
        decorators = [vy_nodes.Name(id="external", node_id=next_nodeid(), ast_type='Name')]
        new_body = []
        fn_body = [dasy.parse.parse_node(body_node) for body_node in body]
        fn_body = process_body(fn_body)

    match fn_tree[1:]:
        case models.Symbol(sym_node), models.List(args_node), returns, decs, *body if isinstance(decs, models.Keyword) or isinstance(decs, models.List):
            # (defn name [args] :uint256 :external ...)
            # (defn name [args] :uint256 [:external :view] ...)
            assert isinstance(returns, models.Keyword) or isinstance(returns, models.Expression) or isinstance(returns, models.Symbol)
            rets = dasy.parse.parse_node(returns)
            args_list = parse_args_list(args_node)
            args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
            if isinstance(decs, models.Keyword):
                decorators = [vy_nodes.Name(id=str(decs.name), node_id=next_nodeid(), ast_type='Name')]
            elif isinstance(decs, models.List):
                decorators = [vy_nodes.Name(id=str(d.name), node_id=next_nodeid(), ast_type='Name') for d in decs]
            else:
                decorators = []
            new_body = []
            fn_body = [dasy.parse.parse_node(body_node) for body_node in body[:-1]]
            if not has_return(body[-1]):
                value_node = dasy.parse.parse_node(body[-1])
                implicit_return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=next_nodeid())
                fn_body.append(implicit_return_node)
            else:
                fn_body.append(dasy.parse.parse_node(body[-1]))
            fn_body = process_body(fn_body)
        case models.Symbol(sym_node), models.List(args_node), decs, *body:
            args_list = parse_args_list(args_node)
            args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
            if isinstance(decs, models.Keyword):
                decorators = [vy_nodes.Name(id=str(decs.name), node_id=next_nodeid(), ast_type='Name')]
            elif isinstance(decs, models.List):
                decorators = [vy_nodes.Name(id=str(d.name), node_id=next_nodeid(), ast_type='Name') for d in decs]
            else:
                decorators = []
            new_body = []
            fn_body = [dasy.parse.parse_node(body_node) for body_node in body]
            fn_body = process_body(fn_body)
        case _:
            raise Exception(f"Invalid fn form {fn_tree}")
    fn_node = vy_nodes.FunctionDef(args=args, returns=rets, decorator_list=decorators, pos=None, body=fn_body, name=name, node_id=fn_node_id, ast_type='FunctionDef')
    for n in decorators:
        fn_node._children.add(n)
    fn_node._children.add(args)
    for n in fn_body:
        if isinstance(n, vy_nodes.Call):
            expr_node = vy_nodes.Expr(ast_type='Expr', node_id=next_nodeid(), value=n)
            expr_node._children.add(n)
            fn_node._children.add(expr_node)
        else:
            fn_node._children.add(n)
    return fn_node

def parse_declaration(var, typ, value=None):
    target = dasy.parse.parse_node(var)
    is_constant = False
    is_public = False
    is_immutable = False
    match typ:
        case [models.Symbol(e), typ_decl] if str(e) in ["public", "immutable", "constant"]:
            annotation = dasy.parse.parse_node(typ)
            match str(e):
                case "public":
                    is_public = True
                case "immutable":
                    is_immutable = True
                case "constant":
                    is_constant = True
        case models.Expression():
            annotation = dasy.parse.parse_node(typ)
        case models.Keyword():
            annotation = dasy.parse.parse_node(typ)
        case _:
            raise Exception(f"Invalid declaration type {typ}")
    return vy_nodes.VariableDecl(ast_type='VariableDecl', node_id=next_nodeid(), target=target, annotation=annotation, value=value, is_constant=is_constant, is_public=is_public, is_immutable=is_immutable)


def parse_defvars(expr):
    return [parse_declaration(var, typ) for var, typ in pairwise(expr[1:])]

def create_annassign_node(var, typ, value=None) -> vy_nodes.AnnAssign:
    target = dasy.parse.parse_node(var)
    match typ:
        case models.Expression() | models.Keyword() | models.Symbol():
            annotation = dasy.parse.parse_node(typ)
        case _:
            raise Exception(f"Invalid declaration type {typ}")
    return vy_nodes.AnnAssign(ast_type='AnnAssign', node_id=next_nodeid(), target=target, annotation=annotation, value=value)

def create_variabledecl_node(var, typ, value=None) -> vy_nodes.VariableDecl:
    target = dasy.parse.parse_node(var)
    match typ:
        case models.Expression() | models.Keyword() | models.Symbol():
            annotation = dasy.parse.parse_node(typ)
        case _:
            raise Exception(f"Invalid declaration type {typ}")
    return vy_nodes.VariableDecl(ast_type='VariableDecl', node_id=next_nodeid(), target=target, annotation=annotation, value=value)

def parse_variabledecl(expr) -> vy_nodes.VariableDecl:
    node = create_variabledecl_node(expr[1], expr[2], value=dasy.parse.parse_node(expr[3]) if len(expr) == 4 else None)
    return node

def parse_annassign(expr) -> vy_nodes.AnnAssign:
    return create_annassign_node(expr[1], expr[2], value=dasy.parse.parse_node(expr[3]) if len(expr) == 4 else None)

def parse_structbody(expr):
    return [create_annassign_node(var, typ) for var, typ in pairwise(expr[2:])]

def parse_contract(expr):
    mod_node = vy_nodes.Module(body=[], name=str(expr[1]), doc_string="", ast_type='Module', node_id=next_nodeid())
    expr_body = []
    match expr[1:]:
        case (_, vars, *body) if isinstance(vars, models.List):
            # # contract has state
            for var, typ in pairwise(vars):
                mod_node.add_to_body(parse_declaration(var, typ))
            expr_body = body
        case (_, *body):
            # no contract state
            expr_body = body
        case _:
            # print(f"no match: {expr}")
            raise Exception(f"Invalid defcontract form: {expr}")
    for node in expr_body:
        mod_node.add_to_body(dasy.parse.parse_node(node))

    return mod_node

def parse_defstruct(expr):
    return vy_nodes.StructDef(ast_type='StructDef', node_id=next_nodeid(), name=str(expr[1]), body=parse_structbody(expr))

def parse_defevent(expr):
    return vy_nodes.EventDef(ast_type='EventDef', node_id=next_nodeid(), name=str(expr[1]), body=parse_structbody(expr))

def parse_do_body(expr):
    calls = [dasy.parse.parse_node(x) for x in expr[1:]]
    exprs = []
    for call_node in calls:
        expr_node = vy_nodes.Expr(ast_type='Expr', node_id=next_nodeid(), value=call_node)
        expr_node._children.add(call_node)
        exprs.append(expr_node)
    return exprs


def parse_subscript(expr):
    """(subscript value slice)"""
    index_value_node = dasy.parse.parse_node(expr[2])
    index_node = vy_nodes.Index(ast_type='Index', node_id=next_nodeid(), value=index_value_node)
    if isinstance(index_value_node, vy_nodes.Tuple):
        index_node._children.add(index_value_node)
    value_node = dasy.parse.parse_node(expr[1])
    subscript_node = vy_nodes.Subscript(ast_type='Subscript', node_id=next_nodeid(), slice=index_node, value=value_node)
    subscript_node._children.add(index_node)
    subscript_node._children.add(value_node)
    return subscript_node
