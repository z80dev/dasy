from .utils import next_nodeid, has_return, pairwise
from hy import models
import dasy
import vyper.ast.nodes as vy_nodes

def parse_fn(fn_tree):
    fn_node_id = next_nodeid()
    assert isinstance(fn_tree, models.Expression)
    assert fn_tree[0] == models.Symbol('defn')
    match fn_tree[1:]:
        case models.Symbol(sym_node), models.List(args_node), returns, models.Keyword(vis), *body:
            assert isinstance(returns, models.Keyword) or isinstance(returns, models.Expression)
            rets = dasy.parse.parse_node(returns)
            name = str(sym_node)
            args_list = dasy.parse.parse_args_list(args_node)
            args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
            decorators = [vy_nodes.Name(id=vis, node_id=next_nodeid(), ast_type='Name')]
            fn_body = [dasy.parse.parse_node(body_node) for body_node in body[:-1]]
            if not has_return(body[-1]):
                value_node = dasy.parse.parse_node(body[-1])
                implicit_return_node = vy_nodes.Return(value=value_node, ast_type='Return', node_id=next_nodeid())
                fn_body.append(implicit_return_node)
            else:
                fn_body.append(dasy.parse.parse_node(body[-1]))
        case models.Symbol(sym_node), models.List(args_node), models.Keyword(vis), *body:
            rets = None
            name = str(sym_node)
            args_list = dasy.parse.parse_args_list(args_node)
            args = vy_nodes.arguments(args=args_list, defaults=list(), node_id=next_nodeid(), ast_type='arguments')
            decorators = [vy_nodes.Name(id=vis, node_id=next_nodeid(), ast_type='Name')]
            fn_body = [dasy.parse.parse_node(body_node) for body_node in body]
        case _:
            raise Exception(f"Invalid fn form {fn_tree}")
    return vy_nodes.FunctionDef(args=args, returns=rets, decorator_list=decorators, pos=None, body=fn_body, name=name, node_id=fn_node_id, ast_type='FunctionDef')

def parse_contract(expr):
    mod_node = vy_nodes.Module(body=[], name=str(expr[1]), doc_string="", ast_type='Module', node_id=next_nodeid())
    expr_body = []
    match expr[1:]:
        case (name, vars, *body) if isinstance(vars, models.List):
            # contract has state
            for var, typ in pairwise(vars):
                target = dasy.parse.parse_node(var)
                is_constant = False
                is_public = False
                is_immutable = False
                match typ:
                    case [models.Symbol(e), typ_decl] if str(e) in ["public", "immutable", "constant"]:
                        annotation = dasy.parse.parse_node(typ)
                        match str(e):
                            case "public":
                                is_public = True
                            case "immutable":
                                is_immutable = True
                            case "constant":
                                is_constant = True
                    case models.Keyword():
                        annotation = dasy.parse.parse_node(typ)
                    case _:
                        raise Exception(f"Invalid declaration type {typ}")
                mod_node.add_to_body(vy_nodes.VariableDecl(ast_type='VariableDecl', node_id=next_nodeid(), target=target, annotation=annotation, value=None, is_constant=is_constant, is_public=is_public, is_immutable=is_immutable))
            expr_body = expr[3:]
        case (name, *body):
            # no contract state
            expr_body = expr[2:]
        case _:
            # print(f"no match: {expr}")
            raise Exception(f"Invalid defcontract form: {expr}")
    for node in expr_body:
        mod_node.add_to_body(dasy.parse.parse_node(node))

    return mod_node
