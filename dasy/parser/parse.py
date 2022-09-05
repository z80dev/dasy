import ast as py_ast

import hy
import rich
import vyper.ast.nodes as vy_nodes
from hy import models

from .builtins import parse_builtin
from .core import (parse_annassign, parse_attribute, parse_call, parse_contract,
                   parse_defvars, parse_do_body, parse_defn, parse_defstruct, parse_for, parse_subscript, parse_tuple, parse_variabledecl)
from .ops import (BIN_FUNCS, BOOL_OPS, COMP_FUNCS, UNARY_OPS, parse_binop,
                  parse_boolop, parse_comparison, parse_unary)
from .stmt import parse_setv, parse_if, parse_return
from .utils import next_node_id_maker, next_nodeid

BUILTIN_FUNCS = BIN_FUNCS + COMP_FUNCS + UNARY_OPS + BOOL_OPS

NAME_CONSTS = ["True", "False"]

MACROS = []

CONSTS = {}

def parse_expr(expr):

    cmd_str = str(expr[0])

    if cmd_str in BIN_FUNCS:
        return parse_binop(expr)
    if cmd_str in COMP_FUNCS:
        return parse_comparison(expr)
    if cmd_str in UNARY_OPS:
        return parse_unary(expr)
    if cmd_str in BOOL_OPS:
        return parse_boolop(expr)

    match cmd_str:
        case "defcontract":
            return parse_contract(expr)
        case "defconst":
            CONSTS[str(expr[1])] = expr[2]
            return None
        case "defmacro":
            hy.eval(expr)
            MACROS.append(str(expr[1]))
            return None
        case str(cmd) if cmd in MACROS:
            new_node = hy.macroexpand(expr)
            return parse_node(new_node)
        case str(cmd) if cmd.startswith('.') and len(cmd) > 1:
            inner_node = models.Expression((models.Symbol('.'), expr[1], (cmd[1:])))
            outer_node = models.Expression((inner_node, *expr[2:]))
            return parse_node(outer_node)
        case 'defn':
            fn_node = parse_defn(expr)
            return fn_node
        case 'return':
            return parse_return(expr)
        case 'quote' | 'tuple':
            return parse_tuple(expr)
        case '.':
            return parse_attribute(expr)
        case 'setv':
            return parse_setv(expr)
        case 'if':
            return parse_if(expr)
        case 'defvars':
            return parse_defvars(expr)
        case 'defstruct':
            return parse_defstruct(expr)
        case 'subscript' | 'array' | 'get-in':
            return parse_subscript(expr)
        case 'for':
            return parse_for(expr)
        case 'annassign' | 'defvar':
            return parse_annassign(expr)
        case 'variabledecl':
            return parse_variabledecl(expr)
        case 'do':
            return parse_do_body(expr)
        case _:
            return parse_call(expr)


def parse_node(node):
    match node:
        case models.Expression(node):
            return parse_expr(node)
        case models.Integer(node):
            return vy_nodes.Int(value=int(node), node_id=next_nodeid(), ast_type='Int')
        case models.Float(node):
            raise Exception("Floating point not supported (yet)")
            # value_node = vy_nodes.Decimal(value=Decimal(float(node)), node_id=next_nodeid(), ast_type='Decimal')
            # return value_node
        case models.String(node):
            return vy_nodes.Str(value=str(node), node_id=next_nodeid(), ast_type='Str')
        case models.Symbol(node) if str(node) in CONSTS.keys():
            return parse_node(CONSTS[str(node)])
        case models.Symbol(node) if str(node) in BUILTIN_FUNCS:
            return parse_builtin(node)
        case models.Symbol(node) if str(node) in NAME_CONSTS:
            return vy_nodes.NameConstant(value=py_ast.literal_eval(str(node)), id=next_nodeid(), ast_type='NameConstant')
        case models.Symbol(node) if str(node).startswith('0x'):
            return vy_nodes.Hex(id=next_nodeid(), ast_type='Hex', value=str(node))
        case models.Symbol(node) if "/" in str(node):
            target, attr = str(node).split('/')
            replacement_node = models.Expression((models.Symbol('.'), models.Symbol(target), models.Symbol(attr)))
            return parse_node(replacement_node)
        case models.Symbol(node) | models.Keyword(node):
            name_node = vy_nodes.Name(id=str(node), node_id=next_nodeid(), ast_type='Name')
            return name_node
        case models.Bytes(byt):
            bytes_node = vy_nodes.Bytes(node_id=next_nodeid(), ast_type='Byte', value=byt)
            return bytes_node
        case models.List(lst):
            list_node = vy_nodes.List(node_id=next_nodeid(), ast_type='List', elements=[])
            for elmt in lst:
                node = parse_node(elmt)
                list_node._children.add(node)
                list_node.elements.append(node)
            return list_node
        case None:
            return None
        case _:
            raise Exception(f"No match for node {node}")

def parse_src(src: str):
    mod_node = vy_nodes.Module(body=[], name="", doc_string="", ast_type='Module', node_id=next_nodeid())

    vars = []
    fs = []
    for element in hy.read_many(src):
        ast = parse_node(element)

        if isinstance(ast, vy_nodes.Module):
            mod_node = ast
        elif isinstance(ast, vy_nodes.VariableDecl):
            vars.append(ast)
        elif isinstance(ast, vy_nodes.StructDef):
            vars.append(ast)
        elif isinstance(ast, vy_nodes.FunctionDef):
            fs.append(ast)
        elif isinstance(ast, list):
            for v in ast:
                vars.append(v)
        elif isinstance(ast, vy_nodes.AnnAssign):
            # top-level AnnAssign nodes should be replaced with a VariableDecl
            is_public = False
            is_immutable = False
            is_constant = False
            if isinstance(ast.annotation, vy_nodes.Call):
                is_public = ast.annotation.func == "public"
                is_immutable = ast.annotation.func == "immutable"
                is_constant = ast.annotation.func == "constant"
            new_node = vy_nodes.VariableDecl(ast_type='VariableDecl', node_id=next_nodeid(), target=ast.target, annotation=ast.annotation, value=ast.value, is_constant=is_constant, is_public=is_public, is_immutable=is_immutable)
            vars.append(new_node)
        elif ast is None:
            # macro declarations return None
            pass
        else:
            raise Exception(f"Unrecognized top-level form {element} {ast}")

    for e in vars + fs:
        mod_node.add_to_body(e)
        mod_node._children.add(e)


    return mod_node

def install_builtin_macros():
    with open("dasy/parser/macros.hy", encoding="utf-8") as f:
        code = f.read()
        for expr in hy.read_many(code):
            parse_node(expr)

install_builtin_macros()
