import ast as py_ast

from typing import Union

from dasy.parser.macros import handle_macro, is_macro


import hy
import vyper.ast.nodes as vy_nodes
from hy import models

from .builtins import parse_builtin, build_node
from .ops import BIN_FUNCS, BOOL_OPS, COMP_FUNCS, UNARY_OPS, is_op, parse_op
from .utils import add_src_map

# namespaces with expression handlers
from . import nodes, core, macros
from dasy.builtin import functions

BUILTIN_FUNCS = BIN_FUNCS | COMP_FUNCS | UNARY_OPS | BOOL_OPS | {"in", "notin"}

NAME_CONSTS = ["True", "False"]

CONSTS = {}

ALIASES = {
    ".": "attribute",
    "quote": "tuple",
    "array": "subscript",
    "defvar": "annassign",
    "setv": "assign",
    "+!": "unsafe_add",
    "-!": "unsafe_sub",
    "*!": "unsafe_mul",
    "/!": "unsafe_div",
    "def": "annassign",
}

SRC = ""


def convert_annassign(ast):
    # top-level AnnAssign nodes should be replaced with a VariableDecl
    is_public = False
    is_immutable = False
    is_constant = False
    if isinstance(ast.annotation, vy_nodes.Call):
        match ast.annotation.func:
            case "public":
                is_public = True
            case "immutable":
                is_immutable = True
            case "constant":
                is_constant = True
    new_node = build_node(
        vy_nodes.VariableDecl,
        target=ast.target,
        annotation=ast.annotation,
        value=ast.value,
        is_constant=is_constant,
        is_public=is_public,
        is_immutable=is_immutable,
    )
    for child in ast.get_children():
        new_node._children.add(child)
        child._parent = new_node
    return new_node


DONT_REPLACE = ("tuple",)


def parse_expr(expr):
    cmd_str = ALIASES.get(str(expr[0]), str(expr[0]))

    if cmd_str != str(expr[0]) and cmd_str not in DONT_REPLACE:
        expr = models.Expression((models.Symbol(cmd_str), *expr[1:]))

    if is_op(cmd_str):
        return parse_op(expr, cmd_str)

    if cmd_str in nodes.handlers:
        return nodes.handlers[cmd_str](expr)

    node_fn = f"parse_{cmd_str}"

    for ns in [nodes, core, macros, functions]:
        if hasattr(ns, node_fn):
            return getattr(ns, node_fn)(expr)

    if is_macro(cmd_str):
        return handle_macro(expr)

    if cmd_str.startswith("."):
        inner_node = models.Expression((models.Symbol("."), expr[1], (cmd_str[1:])))
        outer_node = models.Expression((inner_node, *expr[2:]))
        return parse_node(outer_node)

    match cmd_str:
        case "defconst":
            CONSTS[str(expr[1])] = expr[2]
            return None
        case "defimmutable" | "defimm":
            CONSTS[str(expr[1])] = None
            return None
        case "+=" | "-=" | "*=" | "/=":
            return parse_augop(expr)
        case _:
            return parse_call(expr)


def parse_augop(expr):
    op = models.Symbol(str(expr[0])[:1])
    target, value = expr[1:]
    parsed_code = build_node(
        vy_nodes.AugAssign,
        op=parse_node(op),
        target=parse_node(target),
        value=parse_node(value),
    )
    return parsed_code


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
                    val_node = parse_node(val_arg)
                    kw_node = build_node(
                        vy_nodes.keyword, arg=str(cur_arg)[1:], value=val_node
                    )
                    kw_args.append(kw_node)
                    i += 2
                else:
                    val_node = parse_node(args[i])
                    args_list.append(val_node)
                    i += 1
            func_node = parse_node(fn_name)
            call_node = build_node(
                vy_nodes.Call, func=func_node, args=args_list, keywords=kw_args
            )
            if wrap_expr:
                expr_node = build_node(vy_nodes.Expr, value=call_node)
                return expr_node
            return call_node


def parse_node(
    node: Union[
        models.Expression,
        models.Integer,
        models.String,
        models.Symbol,
        models.Keyword,
        models.Bytes,
        models.List,
    ]
):
    """
    This function converts a node into its corresponding AST node based on its type.
    :param node: A node of the parsed model
    :return: Corresponding AST node, if the node type is supported. Raises exception otherwise.
    """
    # Initialize ast_node to None
    ast_node = None

    # dispatch on type of parsed model
    match node:
        case models.Expression(node):
            ast_node = parse_expr(node)
        case models.Integer(node):
            ast_node = build_node(vy_nodes.Int, value=int(node))
        case models.String(node):
            ast_node = build_node(vy_nodes.Str, value=str(node))
        case models.Symbol(node):
            str_node = str(node)
            str_node = ALIASES.get(str_node, str_node)
            if str_node in CONSTS:
                ast_node = parse_node(CONSTS[str(node)])
            elif str_node in BUILTIN_FUNCS:
                ast_node = parse_builtin(node)
            elif str_node in NAME_CONSTS:
                ast_node = build_node(
                    vy_nodes.NameConstant, value=py_ast.literal_eval(str(node))
                )
            elif str_node.startswith("0x"):
                ast_node = build_node(vy_nodes.Hex, value=str_node)
            elif "/" in str_node:
                target, attr = str(node).split("/")
                replacement_node = models.Expression(
                    (models.Symbol("."), models.Symbol(target), models.Symbol(attr))
                )
                ast_node = parse_node(replacement_node)
            elif "." in str_node and len(str_node) > 1:
                target, attr = str(node).split(".")
                replacement_node = models.Expression(
                    (models.Symbol("."), models.Symbol(target), models.Symbol(attr))
                )
                ast_node = parse_node(replacement_node)
            else:
                ast_node = build_node(vy_nodes.Name, id=str(node))
        case models.Keyword(node):
            ast_node = build_node(vy_nodes.Name, id=str(node))
        case models.Bytes(byt):
            ast_node = build_node(vy_nodes.Bytes, value=byt)
        case models.List(lst):
            ast_node = build_node(
                vy_nodes.List, elements=[parse_node(elmt) for elmt in lst]
            )
        case models.Float(node):
            raise NotImplementedError("Floating point not supported (yet)")
        case _:
            raise ValueError(f"No match for node {node}. Unsupported node type.")
    return add_src_map(SRC, node, ast_node)


def parse_src(src: str):
    global SRC
    SRC = src
    mod_node: vy_nodes.Module = build_node(
        vy_nodes.Module, body=[], name="", doc_string=""
    )

    vars = []
    fs = []
    for element in hy.read_many(src):
        # parse each top-level form
        ast = parse_node(element)

        if isinstance(ast, list):
            for v in ast:
                add_src_map(src, element, v)
        elif ast:
            add_src_map(src, element, ast)
        else:
            continue

        if isinstance(ast, vy_nodes.Module):
            mod_node = ast
        elif isinstance(
            ast,
            (
                vy_nodes.VariableDecl,
                vy_nodes.StructDef,
                vy_nodes.EventDef,
                vy_nodes.InterfaceDef,
                vy_nodes.EnumDef,
            ),
        ):
            vars.append(ast)
        elif isinstance(ast, vy_nodes.FunctionDef):
            fs.append(ast)
        elif isinstance(ast, list):
            for var in ast:
                var_node = var
                if isinstance(var, vy_nodes.AnnAssign):
                    var_node = convert_annassign(var)
                elif isinstance(var, vy_nodes.FunctionDef):
                    fs.append(var)
                    continue
                vars.append(var_node)
        elif isinstance(ast, vy_nodes.AnnAssign):
            new_node = convert_annassign(ast)
            vars.append(new_node)
        else:
            raise Exception(f"Unrecognized top-level form {element} {ast}")

    for e in vars + fs:
        mod_node.add_to_body(e)

    return mod_node
