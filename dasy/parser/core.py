from ast import Expression

import dasy
import vyper.ast.nodes as vy_nodes
from vyper.ast.utils import dict_to_ast
from hy import models

from .utils import has_return, next_nodeid, pairwise


def parse_augop(expr):
    op = models.Symbol(str(expr[0])[:1])
    target = expr[1]
    value = expr[2]
    parsed_code = vy_nodes.AugAssign(
        node_id=next_nodeid(),
        ast_type="AugAssign",
        op=dasy.parser.parse_node(op),
        target=dasy.parser.parse_node(target),
        value=dasy.parser.parse_node(value),
    )
    return parsed_code


def parse_attribute(expr):
    match expr[1:]:
        case [obj, attr]:
            value_node = dasy.parser.parse_node(obj)
            # attr_node = vy_nodes.Attribute(ast_type='Attribute', node_id=next_nodeid(), attr=str(attr), value=value_node)
            attr_node = dict_to_ast(
                {
                    "ast_type": "Attribute",
                    "attr": str(attr),
                    "value": value_node,
                    "node_id": next_nodeid(),
                }
            )
            attr_node._children.add(value_node)
            value_node._parent = attr_node
            return attr_node


def parse_call(expr, wrap_expr=False):
    match expr:
        case (fn_name, *args):
            args_list = []
            kw_args = []
            i = 0
            while i < len(args):
                cur_arg = args[i]
                if (
                    isinstance(cur_arg, models.Keyword)
                    and len(args) > (i + 1)
                    and not isinstance(args[i + 1], models.Keyword)
                ):
                    # TODO: remove this ugly hack and properly check against builtin types
                    # or reconsider whether we should be using keywords for builtin types at all
                    val_arg = args[i + 1]
                    val_node = dasy.parser.parse_node(val_arg)
                    kw_node = vy_nodes.keyword(
                        node_id=next_nodeid(),
                        ast_type="keyword",
                        arg=str(cur_arg)[1:],
                        value=val_node,
                    )
                    kw_args.append(kw_node)
                    i += 2
                else:
                    val_node = dasy.parser.parse_node(args[i])
                    args_list.append(val_node)
                    i += 1
            func_node = dasy.parser.parse_node(fn_name)
            call_node = vy_nodes.Call(
                func=func_node,
                args=args_list,
                keywords=kw_args,
                ast_type="Call",
                node_id=next_nodeid(),
            )
            call_node._children.add(func_node)
            func_node._parent = call_node
            for a in args_list:
                call_node._children.add(a)
                a._parent = call_node
            if wrap_expr:
                expr_node = vy_nodes.Expr(
                    ast_type="Expr", node_id=next_nodeid(), value=call_node
                )
                expr_node._children.add(call_node)
                call_node._parent = expr_node
                return expr_node
            return call_node


def parse_tuple(tuple_tree):
    match tuple_tree:
        case models.Symbol(q), elements if str(q) == "quote":
            elts = [dasy.parser.parse_node(e) for e in elements]
            tuple_node = vy_nodes.Tuple(
                elements=elts, node_id=next_nodeid(), ast_type="Tuple"
            )
            return tuple_node
        case models.Symbol(q), *elements if str(q) == "tuple":
            elts = [dasy.parser.parse_node(e) for e in elements]
            tuple_node = vy_nodes.Tuple(
                elements=elts, node_id=next_nodeid(), ast_type="Tuple"
            )
            return tuple_node
        case _:
            raise Exception(
                "Invalid tuple declaration; requires quoted list or tuple-fn ex: '(2 3 4)/(tuple 2 3 4)"
            )


def parse_args_list(args_list) -> list[vy_nodes.arg]:
    if len(args_list) == 0:
        return []
    results = []
    current_type = args_list[0]
    assert isinstance(current_type, models.Keyword) or isinstance(
        current_type, models.Expression
    )
    # get annotation and name
    for arg in args_list[1:]:
        # check if we hit a new type
        if isinstance(arg, models.Keyword) or isinstance(arg, models.Expression):
            current_type = arg
            continue
        # get annotation and name
        if isinstance(current_type, models.Keyword):
            annotation_node = vy_nodes.Name(
                id=str(current_type.name),
                parent=None,
                node_id=next_nodeid(),
                ast_type="Name",
            )
        elif isinstance(current_type, models.Expression):
            annotation_node = dasy.parse.parse_node(current_type)
        arg_node = vy_nodes.arg(
            arg=str(arg), parent=None, annotation=annotation_node, node_id=next_nodeid()
        )
        arg_node._children.add(annotation_node)
        annotation_node._parent = arg_node
        results.append(arg_node)
    return results


def process_body(body, parent=None):
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
                    expr_node = vy_nodes.Expr(
                        ast_type="Expr", node_id=next_nodeid(), value=f2
                    )
                    expr_node._children.add(f2)
                    f2._parent = expr_node
                    new_body.append(expr_node)
                else:
                    new_body.append(f2)
        elif isinstance(f, vy_nodes.Call):
            expr_node = vy_nodes.Expr(ast_type="Expr", node_id=next_nodeid(), value=f)
            expr_node._children.add(f)
            f._parent = expr_node
            new_body.append(expr_node)
        else:
            new_body.append(f)
    if parent is not None:
        for e in new_body:
            parent._children.add(e)
            e._parent = parent
    return new_body


def parse_defn(fn_tree):
    fn_node_id = next_nodeid()
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol("defn")
    rets = None
    name = str(fn_tree[1])
    args = None
    decorators = []

    if str(fn_tree[1]) == "__init__":
        args_node, decs, *body = fn_tree[2:]
        args_list = parse_args_list(args_node)
        args = vy_nodes.arguments(
            args=args_list, defaults=list(), node_id=next_nodeid(), ast_type="arguments"
        )
        decorators = [
            vy_nodes.Name(id="external", node_id=next_nodeid(), ast_type="Name")
        ]
        fn_body = [dasy.parse.parse_node(body_node) for body_node in body]
        fn_body = process_body(fn_body)

    match fn_tree[1:]:
        case models.Symbol(sym_node), models.List(
            args_node
        ), returns, decs, *body if isinstance(decs, models.Keyword) or isinstance(
            decs, models.List
        ):
            # (defn name [args] :uint256 :external ...)
            # (defn name [args] :uint256 [:external :view] ...)
            assert (
                isinstance(returns, models.Keyword)
                or isinstance(returns, models.Expression)
                or isinstance(returns, models.Symbol)
            )
            rets = dasy.parse.parse_node(returns)
            args_list = parse_args_list(args_node)
            args = vy_nodes.arguments(
                args=args_list,
                defaults=list(),
                node_id=next_nodeid(),
                ast_type="arguments",
            )
            if isinstance(decs, models.Keyword):
                decorators = [
                    vy_nodes.Name(
                        id=str(decs.name), node_id=next_nodeid(), ast_type="Name"
                    )
                ]
            elif isinstance(decs, models.List):
                # decorators = [vy_nodes.Name(id=str(d.name), node_id=next_nodeid(), ast_type='Name') for d in decs]
                decorators = [dasy.parse.parse_node(d) for d in decs]
            else:
                decorators = []
            fn_body = [dasy.parse.parse_node(body_node) for body_node in body[:-1]]
            if not has_return(body[-1]):
                value_node = dasy.parse.parse_node(body[-1])
                implicit_return_node = vy_nodes.Return(
                    value=value_node, ast_type="Return", node_id=next_nodeid()
                )
                fn_body.append(implicit_return_node)
            else:
                fn_body.append(dasy.parse.parse_node(body[-1]))
            fn_body = process_body(fn_body)
        case models.Symbol(sym_node), models.List(args_node), decs, *body:
            args_list = parse_args_list(args_node)
            args = vy_nodes.arguments(
                args=args_list,
                defaults=list(),
                node_id=next_nodeid(),
                ast_type="arguments",
            )
            for arg in args_list:
                args._children.add(arg)
                arg._parent = args
            if isinstance(decs, models.Keyword):
                decorators = [
                    vy_nodes.Name(
                        id=str(decs.name), node_id=next_nodeid(), ast_type="Name"
                    )
                ]
            elif isinstance(decs, models.List):
                # decorators = [vy_nodes.Name(id=str(d.name), node_id=next_nodeid(), ast_type='Name') for d in decs]
                decorators = [dasy.parse.parse_node(d) for d in decs]
            else:
                decorators = []
            fn_body = [dasy.parse.parse_node(body_node) for body_node in body]
            fn_body = process_body(fn_body)
        case _:
            raise Exception(f"Invalid fn form {fn_tree}")

    fn_node = vy_nodes.FunctionDef(
        args=args,
        returns=rets,
        decorator_list=decorators,
        pos=None,
        body=fn_body,
        name=name,
        node_id=fn_node_id,
        ast_type="FunctionDef",
    )

    for n in decorators:
        fn_node._children.add(n)
        n._parent = fn_node
    fn_node._children.add(args)
    args._parent = fn_node

    for n in fn_body:
        if isinstance(n, vy_nodes.Call):
            expr_node = vy_nodes.Expr(ast_type="Expr", node_id=next_nodeid(), value=n)
            expr_node._children.add(n)
            n._parent = expr_node
            fn_node._children.add(expr_node)
            expr_node.parent = fn_node
        else:
            fn_node._children.add(n)
            n._parent = fn_node
    return fn_node


def parse_declaration(var, typ, value=None):
    target = dasy.parse.parse_node(var)
    is_constant = False
    is_public = False
    is_immutable = False
    match typ:
        case [models.Symbol(e), typ_decl] if str(e) in [
            "public",
            "immutable",
            "constant",
        ]:
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
    vdecl_node = vy_nodes.VariableDecl(
        ast_type="VariableDecl",
        node_id=next_nodeid(),
        target=target,
        annotation=annotation,
        value=value,
        is_constant=is_constant,
        is_public=is_public,
        is_immutable=is_immutable,
    )
    vdecl_node._children.add(target)
    target._parent = vdecl_node
    vdecl_node._children.add(annotation)
    annotation._parent = vdecl_node
    if value is not None:
        vdecl_node._children.add(value)
        value._parent = vdecl_node
    return vdecl_node


def parse_defvars(expr):
    return [parse_declaration(var, typ) for var, typ in pairwise(expr[1:])]


def create_annassign_node(var, typ, value=None) -> vy_nodes.AnnAssign:
    target = dasy.parse.parse_node(var)
    match typ:
        case models.Expression() | models.Keyword() | models.Symbol():
            annotation = dasy.parse.parse_node(typ)
        case _:
            raise Exception(f"Invalid declaration type {typ}")
    annassign_node = vy_nodes.AnnAssign(
        ast_type="AnnAssign",
        node_id=next_nodeid(),
        target=target,
        annotation=annotation,
        value=value,
    )
    if target is not None:
        annassign_node._children.add(target)
        target._parent = annassign_node
    if annotation is not None:
        annassign_node._children.add(annotation)
        annotation._parent = annassign_node
    if value is not None:
        annassign_node._children.add(value)
        value._parent = annassign_node
    return annassign_node


def create_variabledecl_node(var, typ, value=None) -> vy_nodes.VariableDecl:
    target = dasy.parse.parse_node(var)
    match typ:
        case models.Expression() | models.Keyword() | models.Symbol():
            annotation = dasy.parse.parse_node(typ)
        case _:
            raise Exception(f"Invalid declaration type {typ}")
    vdecl_node = vy_nodes.VariableDecl(
        ast_type="VariableDecl",
        node_id=next_nodeid(),
        target=target,
        annotation=annotation,
        value=value,
    )
    vdecl_node._children.add(target)
    target._parent = vdecl_node
    vdecl_node._children.add(annotation)
    annotation._parent = vdecl_node
    if value is not None:
        vdecl_node._children.add(value)
        value._parent = vdecl_node


def parse_variabledecl(expr) -> vy_nodes.VariableDecl:
    node = create_variabledecl_node(
        expr[1],
        expr[2],
        value=dasy.parse.parse_node(expr[3]) if len(expr) == 4 else None,
    )
    return node


def parse_annassign(expr) -> vy_nodes.AnnAssign:
    return create_annassign_node(
        expr[1],
        expr[2],
        value=dasy.parse.parse_node(expr[3]) if len(expr) == 4 else None,
    )


def parse_structbody(expr):
    return [create_annassign_node(var, typ) for var, typ in pairwise(expr[2:])]


def parse_defcontract(expr):
    mod_node = vy_nodes.Module(
        body=[],
        name=str(expr[1]),
        doc_string="",
        ast_type="Module",
        node_id=next_nodeid(),
    )
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
            raise Exception(f"Invalid defcontract form: {expr}")
    for node in expr_body:
        mod_node.add_to_body(dasy.parse.parse_node(node))

    return mod_node


def parse_defstruct(expr):
    body = parse_structbody(expr)
    struct_node = vy_nodes.StructDef(
        ast_type="StructDef", node_id=next_nodeid(), name=str(expr[1]), body=body
    )
    for b in body:
        struct_node._children.add(b)
        b._parent = struct_node
    return struct_node


def parse_definterface(expr):
    name = str(expr[1])
    body = []
    for f in expr[2:]:
        fn_node_id = next_nodeid()
        rets = None
        fn_name = str(f[1])
        args = None
        decorators = []

        args_list = parse_args_list(f[2])
        args = vy_nodes.arguments(
            args=args_list, defaults=list(), node_id=next_nodeid(), ast_type="arguments"
        )
        if len(f) == 5:
            # have return
            rets = dasy.parse.parse_node(f[3])
        vis_node = dasy.parse.parse_node(f[-1])
        expr_node = vy_nodes.Expr(
            node_id=next_nodeid(), ast_type="Expr", value=vis_node
        )
        expr_node._children.add(vis_node)
        vis_node._parent = expr_node
        fn_body = [expr_node]
        fn_node = vy_nodes.FunctionDef(
            args=args,
            returns=rets,
            decorator_list=decorators,
            pos=None,
            body=fn_body,
            name=fn_name,
            node_id=fn_node_id,
            ast_type="FunctionDef",
        )
        fn_node._children.add(expr_node)
        expr_node._parent = fn_node
        for a in args_list:
            fn_node._children.add(a)
            a._parent = fn_node
        body.append(fn_node)

    interface_node = vy_nodes.InterfaceDef(
        ast_type="InterfaceDef", node_id=next_nodeid(), body=body, name=name
    )
    for b in body:
        interface_node._children.add(b)
        b._parent = interface_node
    return interface_node


def parse_defevent(expr):
    return vy_nodes.EventDef(
        ast_type="EventDef",
        node_id=next_nodeid(),
        name=str(expr[1]),
        body=parse_structbody(expr),
    )


def parse_do(expr):
    calls = [dasy.parse.parse_node(x) for x in expr[1:]]
    exprs = []
    for call_node in calls:
        expr_node = vy_nodes.Expr(
            ast_type="Expr", node_id=next_nodeid(), value=call_node
        )
        expr_node._children.add(call_node)
        call_node._parent = expr_node
        exprs.append(expr_node)
    return exprs


def parse_subscript(expr):
    """(subscript value slice)"""
    index_value_node = dasy.parse.parse_node(expr[2])
    index_node = vy_nodes.Index(
        ast_type="Index", node_id=next_nodeid(), value=index_value_node
    )
    if isinstance(index_value_node, vy_nodes.Tuple):
        index_node._children.add(index_value_node)
        index_value_node._parent = index_node
    value_node = dasy.parse.parse_node(expr[1])
    subscript_node = vy_nodes.Subscript(
        ast_type="Subscript", node_id=next_nodeid(), slice=index_node, value=value_node
    )
    subscript_node._children.add(index_node)
    index_node._parent = subscript_node
    subscript_node._children.add(value_node)
    value_node._parent = subscript_node
    return subscript_node
