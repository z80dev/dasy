import hy
import ast as py_ast
import vyper.ast.nodes as vy_nodes
from hy import models
from .utils import next_nodeid
from .ops import BIN_FUNCS, parse_binop, COMP_FUNCS, parse_comparison, UNARY_OPS, BOOL_OPS, parse_unary, parse_boolop
from .builtins import parse_builtin
from .core import parse_contract, parse_fn, parse_tuple
from .stmt import parse_if, parse_return, parse_assignment

BUILTIN_FUNCS = BIN_FUNCS + COMP_FUNCS + UNARY_OPS + BOOL_OPS

NAME_CONSTS = ["True", "False"]

def parse_attribute(expr):
    match expr[1:]:
        case [obj, attr]:
            return vy_nodes.Attribute(ast_type='Attribute', node_id=next_nodeid(), attr=str(attr), value=parse_node(obj))

def parse_call(expr):
    match expr:
        case (fn_name, *args):
            args_list = [parse_node(arg) for arg in args]
            return vy_nodes.Call(func=parse_node(fn_name), args=args_list, keywords=[], ast_type='Call', node_id=next_nodeid())

def parse_expr(expr):

    match expr:
        case models.Keyword(name), models.Integer(length):
            if str(name) == "string":
                value_node = parse_node(models.Symbol("String"))
            elif str(name) == "bytes":
                value_node = parse_node(models.Symbol("Bytes"))
            annotation = vy_nodes.Subscript(ast_type='Subscript', node_id=next_nodeid(), slice=vy_nodes.Index(ast_type='Index', node_id=next_nodeid(), value=parse_node(length)), value=value_node)
            annotation._children.add(value_node)
            return annotation

    
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
        case 'defn':
            return parse_fn(expr)
        case 'return':
            return parse_return(expr)
        case 'quote':
            return parse_tuple(expr)
        case '.':
            return parse_attribute(expr)
        case 'setv':
            return parse_assignment(expr)
        case 'if':
            return parse_if(expr)
        case _:
            return parse_call(expr)


def parse_node(node):
    match node:
        case models.Expression(node):
            return parse_expr(node)
        case models.Integer(node):
            value_node = vy_nodes.Int(value=int(node), node_id=next_nodeid(), ast_type='Int')
            return value_node
        case models.Float(node):
            raise Exception("Floating point not supported (yet)")
            # value_node = vy_nodes.Decimal(value=Decimal(float(node)), node_id=next_nodeid(), ast_type='Decimal')
            # return value_node
        case models.String(node):
            value_node = vy_nodes.Str(value=str(node), node_id=next_nodeid(), ast_type='Str')
            return value_node
        case models.Symbol(node) if str(node) in BUILTIN_FUNCS:
            return parse_builtin(node)
        case models.Symbol(node) if str(node) in NAME_CONSTS:
            return vy_nodes.NameConstant(value=py_ast.literal_eval(str(node)), id=next_nodeid(), ast_type='NameConstant')
        case models.Symbol(node) if str(node).startswith('0x'):
            return vy_nodes.Hex(id=next_nodeid(), ast_type='Hex', value=str(node))
        case models.Symbol(node) if str(node).startswith("self/"):
            replacement_node = models.Expression((models.Symbol('.'), models.Symbol('self'), models.Symbol(str(node).split('/')[1])))
            return parse_node(replacement_node)
        case models.Symbol(node) | models.Keyword(node):
            name_node = vy_nodes.Name(id=str(node), node_id=next_nodeid(), ast_type='Name')
            return name_node
        case models.Bytes(byt):
            bytes_node = vy_nodes.Bytes(node_id=next_nodeid(), ast_type='Byte', value=byt)
            return bytes_node
        case None:
            return None
        case _:
            raise Exception(f"No match for node {node}")

def parse_src(src: str):
    ast = parse_node(hy.read(src))
    return ast
