import hy
import vyper.ast.nodes as vy_nodes
import vyper.compiler.phases as phases
from vyper.compiler.phases import CompilerData
from hy import models

BUILTIN_FUNCS = ['+', '-']

node_id_counter = 0

def parse_return(return_tree):
    global node_id_counter
    val = return_tree[1]
    value_node = parse_node(val)
    return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=node_id_counter)
    node_id_counter += 1
    return return_node

def parse_binop(binop_tree):
    global node_id_counter
    match str(binop_tree[0]):
        case '+' | '-':
            left = parse_node(binop_tree[1])
            right = parse_node(binop_tree[2])
            op = parse_node(binop_tree[0])
            return vy_nodes.BinOp(left=left, right=right, op=op, node_id=node_id_counter, ast_type='BinOp')

def parse_args_list(args_list) -> [vy_nodes.arg]:
    global node_id_counter
    if len(args_list) == 0:
        return []
    results = []
    current_type = args_list[0]
    assert isinstance(current_type, models.Keyword)
    # get annotation and name
    for arg in args_list[1:]:
        # get annotation and name
        annotation_node = vy_nodes.Name(id=str(current_type.name), parent=None, node_id=node_id_counter, ast_type='Name')
        node_id_counter += 1
        results.append(vy_nodes.arg(arg=str(arg), parent=None, annotation=annotation_node, node_id=node_id_counter))
        node_id_counter += 1
    return results

def parse_fn(fn_tree):
    global node_id_counter
    fn_node_id = node_id_counter
    node_id_counter += 1
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol('defn')
    # name = vy_nodes.Name(id=str(fn_tree[1]), node_id=node_id_counter, ast_type='Name' )
    # node_id_counter += 1
    name = str(fn_tree[1])
    args_list = parse_args_list(fn_tree[2])
    args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=node_id_counter, ast_type='arguments')
    node_id_counter += 1
    rets = vy_nodes.Name(id=fn_tree[3].name, node_id=node_id_counter, ast_type='Name')
    node_id_counter += 1
    decorators = []
    body = []
    for el in fn_tree[4:]:
        if isinstance(el, models.Keyword):
            decorators.append(vy_nodes.Name(id=el.name, node_id=node_id_counter, ast_type='Name'))
            node_id_counter += 1
        elif isinstance(el, models.Expression):
            body.append(parse_node(el))
    return vy_nodes.FunctionDef(args=args, returns=rets, decorator_list=decorators, pos=None, body=body, name=name, node_id=fn_node_id, ast_type='FunctionDef')

def parse_expr(expr):
    global node_id_counter
    match str(expr[0]):
        case "defcontract":
            mod_node = vy_nodes.Module(body=[], name=str(expr[1]), doc_string="", ast_type='Module', node_id=node_id_counter)
            node_id_counter += 1
            for node in expr[2:]:
                mod_node.add_to_body(parse_node(node))
            return mod_node
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
    global node_id_counter
    match str(node):
        case '+':
            op_node = vy_nodes.Add(node_id=node_id_counter, ast_type='Add', _pretty="+", _description="addition")
            node_id_counter += 1
            return op_node
        case '-':
            op_node = vy_nodes.Sub(node_id=node_id_counter, ast_type='Sub', _pretty="-", _description="subtraction")
            node_id_counter += 1
            return op_node


def parse_node(ast_node):
    global node_id_counter
    if isinstance(ast_node, models.Expression):
        return parse_expr(ast_node)
    if isinstance(ast_node, models.Integer):
        value_node = vy_nodes.Int(value=int(ast_node), node_id=node_id_counter, ast_type='Int')
        node_id_counter += 1
        return value_node
    if str(ast_node) in BUILTIN_FUNCS:
        return parse_builtin(ast_node)
    if isinstance(ast_node, models.Symbol):
        name_node = vy_nodes.Name(id=str(ast_node), node_id=node_id_counter, ast_type='Name')
        node_id_counter += 1
        return name_node


def compile(src: str) -> CompilerData:
    ast = parse_node(hy.read(src))
    data = phases.CompilerData("", ast.name, None, source_id=0, )
    data.vyper_module = ast
    return data
