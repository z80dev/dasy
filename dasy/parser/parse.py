import ast as py_ast

from dasy.parser.macros import handle_macro, is_macro


import hy
import vyper.ast.nodes as vy_nodes
from hy import models

from .builtins import parse_builtin
from .core import parse_augop, parse_call
from .ops import BIN_FUNCS, BOOL_OPS, COMP_FUNCS, UNARY_OPS, is_op, parse_op
from .utils import next_nodeid, add_src_map

# namespaces with expression handlers
from . import nodes, core, macros
from dasy.builtin import functions

BUILTIN_FUNCS = BIN_FUNCS + COMP_FUNCS + UNARY_OPS + BOOL_OPS + ["in", "notin"]

NAME_CONSTS = ["True", "False"]

CONSTS = {}

ALIASES = {
    ".": "attribute",
    "quote": "tuple",
    "array": "subscript",
    "defvar": "annassign",
    "setv": "assign",
}

SRC = ""


def parse_expr(expr):

    cmd_str = ALIASES.get(str(expr[0]), str(expr[0]))

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


def parse_node(node):
    ast_node = None

    # dispatch on type of parsed model
    match node:
        case models.Expression(node):
            ast_node = parse_expr(node)
        case models.Integer(node):
            ast_node = vy_nodes.Int(
                value=int(node), node_id=next_nodeid(), ast_type="Int"
            )
        case models.Float(node):
            raise Exception("Floating point not supported (yet)")
            # value_node = vy_nodes.Decimal(value=Decimal(float(node)), node_id=next_nodeid(), ast_type='Decimal')
            # ast_node = value_node
        case models.String(node):
            ast_node = vy_nodes.Str(
                value=str(node), node_id=next_nodeid(), ast_type="Str"
            )
        case models.Symbol(node):
            str_node = str(node)
            if str_node in CONSTS:
                ast_node = parse_node(CONSTS[str(node)])
            elif str_node in BUILTIN_FUNCS:
                ast_node = parse_builtin(node)
            elif str_node in NAME_CONSTS:
                ast_node = vy_nodes.NameConstant(
                    value=py_ast.literal_eval(str(node)),
                    node_id=next_nodeid(),
                    ast_type="NameConstant",
                )
            elif str_node.startswith("0x"):
                ast_node = vy_nodes.Hex(
                    id=next_nodeid(), ast_type="Hex", value=str_node
                )
            elif "/" in str_node:
                target, attr = str(node).split("/")
                replacement_node = models.Expression(
                    (models.Symbol("."), models.Symbol(target), models.Symbol(attr))
                )
                ast_node = parse_node(replacement_node)
            else:
                name_node = vy_nodes.Name(
                    id=str(node), node_id=next_nodeid(), ast_type="Name"
                )
                ast_node = name_node
        case models.Keyword(node):
            name_node = vy_nodes.Name(
                id=str(node), node_id=next_nodeid(), ast_type="Name"
            )
            ast_node = name_node
        case models.Bytes(byt):
            bytes_node = vy_nodes.Bytes(
                node_id=next_nodeid(), ast_type="Byte", value=byt
            )
            ast_node = bytes_node
        case models.List(lst):
            list_node = vy_nodes.List(
                node_id=next_nodeid(), ast_type="List", elements=[]
            )
            for elmt in lst:
                node = parse_node(elmt)
                list_node._children.add(node)
                list_node.elements.append(node)
                node._parent = list_node
            ast_node = list_node
        case None:
            ast_node = None
        case _:
            raise Exception(f"No match for node {node}")
    return add_src_map(SRC, node, ast_node)


def parse_src(src: str):
    global SRC
    SRC = src
    mod_node = vy_nodes.Module(
        body=[], name="", doc_string="", ast_type="Module", node_id=next_nodeid()
    )

    vars = []
    fs = []
    for element in hy.read_many(src):
        # parse each top-level form
        ast = parse_node(element)

        if isinstance(ast, list):
            for v in ast:
                v.full_source_code = src
        elif ast is not None:
            ast.full_source_code = src
            ast.lineno = element.start_line
            ast.end_lineno = element.end_line
            ast.col_offset = element.start_column
            ast.end_col_offset = element.end_column

        match ast:
            case vy_nodes.Module:
                mod_node = ast
            case vy_nodes.VariableDecl() | vy_nodes.StructDef() | vy_nodes.EventDef() | vy_nodes.InterfaceDef():
                vars.append(ast)
            case vy_nodes.FunctionDef():
                fs.append(ast)
            case list():
                for v in ast:
                    vars.append(v)
            case vy_nodes.AnnAssign():
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
                new_node = vy_nodes.VariableDecl(
                    ast_type="VariableDecl",
                    node_id=next_nodeid(),
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
                vars.append(new_node)
            case None:
                pass
            case _:
                raise Exception(f"Unrecognized top-level form {element} {ast}")

    for e in vars + fs:
        mod_node.add_to_body(e)
        mod_node._children.add(e)
        e._parent = mod_node

    return mod_node
