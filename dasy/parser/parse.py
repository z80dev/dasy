import ast as py_ast
import os
from dasy.parser import macros

from dasy.parser.macros import handle_macro, is_macro

from . import nodes

import hy
import vyper.ast.nodes as vy_nodes
from vyper.compiler import phases
from hy import models

# for handling venom
from vyper.ir.s_expressions import parse_s_exp
from vyper.codegen.ir_node import IRnode
from vyper.builtin_functions import STMT_DISPATCH_TABLE, BuiltinFunction

from .builtins import parse_builtin
from .core import (parse_annassign, parse_attribute, parse_augop, parse_call, parse_defcontract, parse_defevent, parse_definterface,
                   parse_defvars, parse_do_body, parse_defn, parse_defstruct, parse_subscript, parse_tuple, parse_variabledecl)
from .ops import (BIN_FUNCS, BOOL_OPS, COMP_FUNCS, UNARY_OPS, is_op, parse_binop,
                  parse_boolop, parse_comparison, parse_op, parse_unary)
from .utils import next_node_id_maker, next_nodeid, add_src_map
from dasy.parser import core

BUILTIN_FUNCS = BIN_FUNCS + COMP_FUNCS + UNARY_OPS + BOOL_OPS + ["in", "notin"]

NAME_CONSTS = ["True", "False"]

CONSTS = {}

ALIASES= {
    '.': 'attribute',
    'quote': 'tuple',
    'array': 'subscript',
    'defvar': 'annassign',
    'setv': 'assign'
}

SRC = ""

def parse_expr(expr):

    cmd_str = ALIASES.get(str(expr[0]), str(expr[0]))

    if is_op(cmd_str):
        return parse_op(expr, cmd_str)

    if cmd_str in nodes.handlers.keys():
        return nodes.handlers[cmd_str](expr)

    node_fn = f"parse_{cmd_str}"

    for ns in [nodes, core, macros]:
        if hasattr(ns, node_fn):
            return getattr(ns, node_fn)(expr)

    if is_macro(cmd_str):
        return handle_macro(expr)

    if cmd_str.startswith('.'):
        inner_node = models.Expression((models.Symbol('.'), expr[1], (cmd_str[1:])))
        outer_node = models.Expression((inner_node, *expr[2:]))
        return parse_node(outer_node)

    match cmd_str:
        case "defconst":
            CONSTS[str(expr[1])] = expr[2]
            return None
        case "defimmutable" | "defimm":
            CONSTS[str(expr[1])] = None
            return None
        case "vyper":
            return phases.generate_ast(str(expr[1]), 0, "").body[0]
        case "venom":
            s_expr = str(expr[1])
            ir = IRnode.from_list((parse_s_exp(expr[1]))[0])
            # generate some vyper code to patch in.
            IDENTIFIER = f"__DASY_VENOM_BUILTIN_{next_nodeid()}__"
            insert_code = f"{IDENTIFIER}()"

            # dynamically generate a class on the fly
            class generated_builtin(BuiltinFunction):
                _id = IDENTIFIER
                _inputs = ()
                _return_type = None
                def build_IR(self, expr, context):
                    return ir

            STMT_DISPATCH_TABLE[IDENTIFIER] = generated_builtin()

            return phases.generate_ast(insert_code, 0, "").body[0]

        case "defmacro":
            hy.eval(expr)
            MACROS.append(str(expr[1]))
            return None
        case '+=' | '-=' | '*=' | '/=':
            return parse_augop(expr)
        case 'do':
            return parse_do_body(expr)
        case _:
            return parse_call(expr)

def parse_node(node):
    ast_node = None
    match node:
        case models.Expression(node):
            ast_node = parse_expr(node)
        case models.Integer(node):
            ast_node = vy_nodes.Int(value=int(node), node_id=next_nodeid(), ast_type='Int')
        case models.Float(node):
            raise Exception("Floating point not supported (yet)")
            # value_node = vy_nodes.Decimal(value=Decimal(float(node)), node_id=next_nodeid(), ast_type='Decimal')
            # ast_node = value_node
        case models.String(node):
            ast_node = vy_nodes.Str(value=str(node), node_id=next_nodeid(), ast_type='Str')
        case models.Symbol(node) if str(node) in CONSTS.keys():
            ast_node = parse_node(CONSTS[str(node)])
        case models.Symbol(node) if str(node) in BUILTIN_FUNCS:
            ast_node = parse_builtin(node)
        case models.Symbol(node) if str(node) in NAME_CONSTS:
            ast_node = vy_nodes.NameConstant(value=py_ast.literal_eval(str(node)), node_id=next_nodeid(), ast_type='NameConstant')
        case models.Symbol(node) if str(node).startswith('0x'):
            ast_node = vy_nodes.Hex(id=next_nodeid(), ast_type='Hex', value=str(node))
        case models.Symbol(node) if "/" in str(node):
            target, attr = str(node).split('/')
            replacement_node = models.Expression((models.Symbol('.'), models.Symbol(target), models.Symbol(attr)))
            ast_node = parse_node(replacement_node)
        case models.Symbol(node) | models.Keyword(node):
            name_node = vy_nodes.Name(id=str(node), node_id=next_nodeid(), ast_type='Name')
            ast_node = name_node
        case models.Bytes(byt):
            bytes_node = vy_nodes.Bytes(node_id=next_nodeid(), ast_type='Byte', value=byt)
            ast_node = bytes_node
        case models.List(lst):
            list_node = vy_nodes.List(node_id=next_nodeid(), ast_type='List', elements=[])
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
    mod_node = vy_nodes.Module(body=[], name="", doc_string="", ast_type='Module', node_id=next_nodeid())

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
                continue
            case vy_nodes.VariableDecl() |  vy_nodes.StructDef() | vy_nodes.EventDef() | vy_nodes.InterfaceDef():
                vars.append(ast)
                continue
            case vy_nodes.FunctionDef():
                fs.append(ast)
                continue
            case list():
                for v in ast:
                    vars.append(v)
                continue
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
                new_node = vy_nodes.VariableDecl(ast_type='VariableDecl', node_id=next_nodeid(), target=ast.target, annotation=ast.annotation, value=ast.value, is_constant=is_constant, is_public=is_public, is_immutable=is_immutable)
                for child in ast.get_children():
                    new_node._children.add(child)
                    child._parent = new_node
                vars.append(new_node)
                continue
            case None:
                continue
            case _:
                raise Exception(f"Unrecognized top-level form {element} {ast}")

    for e in vars + fs:
        mod_node.add_to_body(e)
        mod_node._children.add(e)
        e._parent = mod_node


    return mod_node

def install_builtin_macros():
    macro_file = os.path.join(os.path.dirname(__file__), 'macros.hy')
    with open(macro_file, encoding="utf-8") as f:
        code = f.read()
        for expr in hy.read_many(code):
            parse_node(expr)

install_builtin_macros()
