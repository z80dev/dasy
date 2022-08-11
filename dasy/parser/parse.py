import hy
import vyper.ast.nodes as vy_nodes
import vyper.compiler.phases as phases
from vyper.compiler.phases import CompilerData
from hy import models

BUILTIN_FUNCS = ['+', '-']

def counter_gen():
    _counter = 0
    while True:
        yield _counter
        _counter += 1

def next_node_id_maker():
    counter = counter_gen()

    def next_num():
        return next(counter)

    return next_num


next_nodeid = next_node_id_maker()


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
    name = str(fn_tree[1])
    args_list = parse_args_list(fn_tree[2])
    args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
    rets = vy_nodes.Name(id=fn_tree[3].name, node_id=next_nodeid(), ast_type='Name')

    decorators = []
    body = []
    for el in fn_tree[4:-1]: # all but last
        if isinstance(el, models.Keyword):
            decorators.append(vy_nodes.Name(id=el.name, node_id=next_nodeid(), ast_type='Name'))
        elif isinstance(el, models.Expression):
            body.append(parse_node(el))
    assert isinstance(fn_tree[-1], models.Expression)
    value_node = parse_node(fn_tree[-1])
    implicit_return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=next_nodeid())

    body.append(implicit_return_node)
    return vy_nodes.FunctionDef(args=args, returns=rets, decorator_list=decorators, pos=None, body=body, name=name, node_id=fn_node_id, ast_type='FunctionDef')

def parse_contract(expr):
    match expr[1:]:
        case (name, vars, *body) if isinstance(vars, models.List):
            # print(f"vars match: {expr}")
            mod_node = vy_nodes.Module(body=[], name=str(expr[1]), doc_string="", ast_type='Module', node_id=next_nodeid())

            for node in expr[3:]:
                mod_node.add_to_body(parse_node(node))
            return mod_node
        case (name, *body):
            mod_node = vy_nodes.Module(body=[], name=str(expr[1]), doc_string="", ast_type='Module', node_id=next_nodeid())
            for node in expr[2:]:
                mod_node.add_to_body(parse_node(node))
            return mod_node
        case _:
            # print(f"no match: {expr}")
            raise Exception(f"Invalid defcontract form: {expr}")

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


def parse_node(ast_node):
    global node_id_counter
    if isinstance(ast_node, models.Expression):
        return parse_expr(ast_node)
    if isinstance(ast_node, models.Integer):
        value_node = vy_nodes.Int(value=int(ast_node), node_id=next_nodeid(), ast_type='Int')
        return value_node
    if str(ast_node) in BUILTIN_FUNCS:
        return parse_builtin(ast_node)
    if isinstance(ast_node, models.Symbol):
        name_node = vy_nodes.Name(id=str(ast_node), node_id=next_nodeid(), ast_type='Name')
        return name_node

def parse_src(src: str):
    ast = parse_node(hy.read(src))
    return ast
