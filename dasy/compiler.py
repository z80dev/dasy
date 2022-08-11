import hy
import vyper.ast.nodes as vy_nodes
import vyper.compiler.phases as phases
from vyper.compiler.phases import CompilerData
from hy import models

node_id_counter = 0

def parse_return(return_tree):
    global node_id_counter
    val = return_tree[1]
    if isinstance(val, models.Integer):
        value_node = vy_nodes.Int(value=int(val), node_id=node_id_counter, ast_type='Int')
        node_id_counter += 1
        return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=node_id_counter)
        node_id_counter += 1
        return return_node


def parse_fn(fn_tree):
    global node_id_counter
    fn_node_id = node_id_counter
    node_id_counter += 1
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol('defn')
    name = str(fn_tree[1])
    args = vy_nodes.arguments(args=list(fn_tree[2]), defaults=list(), node_id=node_id_counter, ast_type='arguments')
    node_id_counter += 1
    rets = vy_nodes.Name(id=str(fn_tree[3]), node_id=node_id_counter, ast_type='Name')
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
        case _:
            raise Exception(f"No match for expression cmd {expr[0]}")

def parse_node(ast_node):
    if isinstance(ast_node, models.Expression):
        return parse_expr(ast_node)

def compile(src: str) -> CompilerData:
    ast = parse_node(hy.read(src))
    data = phases.CompilerData("", ast.name, None, source_id=0, )
    data.vyper_module = ast
    return data
