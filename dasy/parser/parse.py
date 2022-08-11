import hy
import vyper.ast.nodes as vy_nodes
import vyper.compiler.phases as phases
from vyper.compiler.phases import CompilerData
from hy import models
from .utils import next_nodeid

BUILTIN_FUNCS = ['+', '-']

def parse_return(return_tree):
    val = return_tree[1]
    value_node = parse_node(val)
    return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=next_nodeid())
    return return_node

def parse_binop(binop_tree):
    match str(binop_tree[0]):
        case '+' | '-':
            left = parse_node(binop_tree[1])
            right = parse_node(binop_tree[2])
            op = parse_node(binop_tree[0])
            return vy_nodes.BinOp(left=left, right=right, op=op, node_id=next_nodeid(), ast_type='BinOp')

def parse_args_list(args_list) -> [vy_nodes.arg]:
    if len(args_list) == 0:
        return []
    results = []
    current_type = args_list[0]
    assert isinstance(current_type, models.Keyword)
    # get annotation and name
    for arg in args_list[1:]:
        # get annotation and name
        annotation_node = vy_nodes.Name(id=str(current_type.name), parent=None, node_id=next_nodeid(), ast_type='Name')
        results.append(vy_nodes.arg(arg=str(arg), parent=None, annotation=annotation_node, node_id=next_nodeid()))
    return results

def parse_fn(fn_tree):
    fn_node_id = next_nodeid()
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol('defn')
    match fn_tree[1:]:
        case models.Symbol(sym_node), models.List(list_node), models.Keyword(ret_node), models.Keyword(vis), *body:
            name = str(sym_node)
            args_list = parse_args_list(list_node)
            args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
            rets = vy_nodes.Name(id=ret_node, node_id=next_nodeid(), ast_type='Name')
            decorators = [vy_nodes.Name(id=vis, node_id=next_nodeid(), ast_type='Name')]
            fn_body = [parse_node(body_node) for body_node in body[:-1]]
            assert isinstance(body[-1], models.Expression)
            value_node = parse_node(body[-1])
            implicit_return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=next_nodeid())
            fn_body.append(implicit_return_node)
        case _:
            raise Exception(f"Invalid fn form {fn_tree}")
    return vy_nodes.FunctionDef(args=args, returns=rets, decorator_list=decorators, pos=None, body=fn_body, name=name, node_id=fn_node_id, ast_type='FunctionDef')

def parse_contract(expr):
    mod_node = vy_nodes.Module(body=[], name=str(expr[1]), doc_string="", ast_type='Module', node_id=next_nodeid())
    expr_body = []
    match expr[1:]:
        case (name, vars, *body) if isinstance(vars, models.List):
            # contract has state
            expr_body = expr[3:]
        case (name, *body):
            # no contract state
            expr_body = expr[2:]
        case _:
            # print(f"no match: {expr}")
            raise Exception(f"Invalid defcontract form: {expr}")
    for node in expr_body:
        mod_node.add_to_body(parse_node(node))

    return mod_node

def parse_expr(expr):
    match str(expr[0]):
        case "defcontract":
            return parse_contract(expr)
        case 'defn':
            return parse_fn(expr)
        case 'return':
            return parse_return(expr)
        case '+' | '-':
            node = parse_binop(expr)
            return node
        case _:
            raise Exception(f"No match for expression cmd {expr[0]}")

def parse_builtin(node):
    match str(node):
        case '+':
            op_node = vy_nodes.Add(node_id=next_nodeid(), ast_type='Add', _pretty="+", _description="addition")
            return op_node
        case '-':
            op_node = vy_nodes.Sub(node_id=next_nodeid(), ast_type='Sub', _pretty="-", _description="subtraction")
            return op_node

def parse_node(node):
    match node:
        case models.Expression(node):
            return parse_expr(node)
        case models.Integer(node):
            value_node = vy_nodes.Int(value=int(node), node_id=next_nodeid(), ast_type='Int')
            return value_node
        case models.Symbol(node) if str(node) in BUILTIN_FUNCS:
            return parse_builtin(node)
        case models.Symbol(node):
            name_node = vy_nodes.Name(id=str(node), node_id=next_nodeid(), ast_type='Name')
            return name_node
        case _:
            raise Exception(f"No match for node {node}")

def parse_src(src: str):
    ast = parse_node(hy.read(src))
    return ast
