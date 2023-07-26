import dasy
import vyper.ast.nodes as vy_nodes
from .utils import build_node, next_nodeid, pairwise
from hy import models

from .utils import has_return, process_body


def parse_attribute(expr):
    """Parses an attribute and builds a node."""
    if len(expr) < 2:
        raise ValueError("Expression too short to parse attribute.")
    _, obj, attr = expr
    attr_node = build_node(
        vy_nodes.Attribute, attr=str(attr), value=dasy.parser.parse_node(obj)
    )
    return attr_node


def parse_tuple(tuple_tree):
    elements = []
    if tuple_tree[0] == models.Symbol("quote"):
        elements = tuple_tree[1]
    elif tuple_tree[0] == models.Symbol("tuple"):
        elements = tuple_tree[1:]
    else:
        raise Exception("Invalid tuple declaration")
    return build_node(
        vy_nodes.Tuple, elements=[dasy.parser.parse_node(e) for e in elements]
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
        if isinstance(arg, (models.Keyword, models.Expression)):
            current_type = arg
            continue
        # get annotation and name
        if isinstance(current_type, models.Keyword):
            # built-in types like :uint256
            annotation_node = build_node(
                vy_nodes.Name, id=str(current_type.name), parent=None
            )
        elif isinstance(current_type, models.Expression):
            # user-defined types like Foo
            annotation_node = dasy.parse.parse_node(current_type)
        else:
            raise Exception("Invalid type annotation")
        arg_node = build_node(
            vy_nodes.arg, arg=str(arg), parent=None, annotation=annotation_node
        )
        results.append(arg_node)
    return results


def parse_fn_args(fn_tree):
    args_node, *rest = fn_tree[2:]
    args_list = parse_args_list(args_node)
    args = build_node(vy_nodes.arguments, args=args_list, defaults=list())
    return args, rest


def parse_fn_decorators(decs):
    if isinstance(decs, models.Keyword):
        return [build_node(vy_nodes.Name, id=str(decs.name))]
    elif isinstance(decs, models.List):
        return [dasy.parse.parse_node(d) for d in decs]
    return []


def parse_fn_body(body, wrap=False):
    fn_body = [dasy.parse.parse_node(body_node) for body_node in body[:-1]]
    if wrap and not has_return(body[-1]):
        value_node = dasy.parse.parse_node(body[-1])
        implicit_return_node = build_node(vy_nodes.Return, value=value_node)
        fn_body.append(implicit_return_node)
    else:
        fn_body.append(dasy.parse.parse_node(body[-1]))
    return process_body(fn_body)


def _fn_tree_has_return_type(fn_tree):
    # has return type
    # (defn name [args] :uint256 :external ...)
    # (defn name [args] :uint256 [:external :view] ...)
    fn_args = fn_tree[1:]
    fn_args_len = len(fn_args)
    return (
        fn_args_len > 3
        and isinstance(fn_args[0], models.Symbol)
        and isinstance(fn_args[1], models.List)
        and isinstance(fn_args[2], (models.Keyword, models.Expression, models.Symbol))
        and isinstance(fn_args[3], (models.Keyword, models.List))
    )


def _fn_tree_has_no_return_type(fn_tree):
    # no return type
    # (defn name [args] ...)
    fn_args = fn_tree[1:]
    fn_args_len = len(fn_args)
    return (
        fn_args_len > 2
        and isinstance(fn_args[0], models.Symbol)
        and isinstance(fn_args[1], models.List)
        and isinstance(fn_args[2], (models.Keyword, models.List))
    )


def _fn_is_constructor(fn_tree):
    return isinstance(fn_tree[1], models.Symbol) and str(fn_tree[1]) == "__init__"


def parse_defn(fn_tree):
    fn_node_id = (
        next_nodeid()
    )  # we want our fn node to have a lower id than its child node
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol("defn")
    return_type = None
    name = str(fn_tree[1])
    args = None
    decorators = []

    fn_args = fn_tree[1:]
    args, rest = parse_fn_args(fn_tree)

    if _fn_is_constructor(fn_tree):
        decorators = [build_node(vy_nodes.Name, id="external")]
        fn_body = parse_fn_body(rest[1:])
    elif _fn_tree_has_return_type(fn_tree):
        decorators = parse_fn_decorators(fn_args[3])
        fn_body = parse_fn_body(rest[2:], wrap=True)
        return_type = dasy.parse.parse_node(fn_args[2])
    elif _fn_tree_has_no_return_type(fn_tree):
        decorators = parse_fn_decorators(fn_args[2])
        fn_body = parse_fn_body(rest[1:])
    else:
        raise Exception(f"Invalid fn form {fn_tree}")

    fn_node = build_node(
        vy_nodes.FunctionDef,
        args=args,
        returns=return_type,
        decorator_list=decorators,
        pos=None,
        body=fn_body,
        name=name,
        node_id=fn_node_id,
    )

    return fn_node


def parse_declaration(var, typ, value=None):
    target = dasy.parse.parse_node(var)
    annotation_attrs = {"public": False, "immutable": False, "constant": False}
    annotation = None

    match typ:
        case [models.Symbol(e), _] if str(e) in annotation_attrs.keys():
            annotation = dasy.parse.parse_node(typ)
            annotation_attrs[str(e)] = True
        case models.Expression() | models.Keyword():
            annotation = dasy.parse.parse_node(typ)
        case _:
            raise Exception(f"Invalid declaration type {typ}")

    if annotation is None:
        raise Exception(f"No valid annotation was found")

    vdecl_node = build_node(
        vy_nodes.VariableDecl,
        target=target,
        annotation=annotation,
        value=value,
        **annotation_attrs,
    )
    return vdecl_node


def parse_defvars(expr):
    return [parse_declaration(var, typ) for var, typ in pairwise(expr[1:])]


def create_annotated_node(node_class, var, typ, value=None):
    target = dasy.parse.parse_node(var)
    if not isinstance(typ, (models.Expression, models.Keyword, models.Symbol)):
        raise Exception(f"Invalid declaration type {typ}")
    annotation = dasy.parse.parse_node(typ)
    node = build_node(node_class, target=target, annotation=annotation, value=value)
    return node


def parse_variabledecl(expr) -> vy_nodes.VariableDecl:
    return create_annotated_node(
        vy_nodes.VariableDecl,
        expr[1],
        expr[2],
        value=dasy.parse.parse_node(expr[3]) if len(expr) == 4 else None,
    )


def parse_annassign(expr) -> vy_nodes.AnnAssign:
    return create_annotated_node(
        vy_nodes.AnnAssign,
        expr[1],
        expr[2],
        value=dasy.parse.parse_node(expr[3]) if len(expr) == 4 else None,
    )


def parse_structbody(expr):
    return [
        create_annotated_node(vy_nodes.AnnAssign, var, typ)
        for var, typ in pairwise(expr[2:])
    ]


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
    struct_node = build_node(
        vy_nodes.StructDef, name=str(expr[1]), body=parse_structbody(expr)
    )
    return struct_node


def parse_definterface(expr):
    name = str(expr[1])
    body = []
    for f in expr[2:]:
        rets = None if len(f) == 4 else dasy.parse.parse_node(f[3])

        args_list = parse_args_list(f[2])
        args_node = build_node(vy_nodes.arguments, args=args_list, defaults=list())

        # in an interface, the body is a single expr node with the visibility
        visibility_node = dasy.parse.parse_node(f[-1])
        body_node = build_node(vy_nodes.Expr, value=visibility_node)

        fn_node = build_node(
            vy_nodes.FunctionDef,
            args=args_node,
            returns=rets,
            decorator_list=[],
            pos=None,
            body=[body_node],
            name=str(f[1]),
        )
        body.append(fn_node)

    interface_node = build_node(vy_nodes.InterfaceDef, body=body, name=name)
    return interface_node


def parse_defevent(expr):
    return build_node(vy_nodes.EventDef, name=str(expr[1]), body=parse_structbody(expr))


def parse_enumbody(expr):
    return [build_node(vy_nodes.Expr, value=dasy.parse.parse_node(x)) for x in expr[2:]]


def parse_defenum(expr):
    return build_node(vy_nodes.EnumDef, name=str(expr[1]), body=parse_enumbody(expr))


def parse_do(expr):
    calls = [dasy.parse.parse_node(x) for x in expr[1:]]
    exprs = [build_node(vy_nodes.Expr, value=call_node) for call_node in calls]
    return exprs


def parse_subscript(expr):
    """(subscript value slice)"""
    index_value_node = dasy.parse.parse_node(expr[2])
    index_node = build_node(vy_nodes.Index, value=index_value_node)
    value_node = dasy.parse.parse_node(expr[1])
    subscript_node = build_node(vy_nodes.Subscript, slice=index_node, value=value_node)
    return subscript_node
