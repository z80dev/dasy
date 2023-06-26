from hy import models
import vyper.ast.nodes as vy_nodes
from .builtins import build_node

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

def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)


def has_return(tree):
    match tree:
        case models.Symbol(sym) if str(sym) == "return":
            return True
        case models.Sequence(seq):
            for el in seq:
                if has_return(el):
                    return True
        case _:
            return False
    return False




def add_src_map(src_code, element, ast_node):
    if ast_node is None:
        return None
    if isinstance(ast_node, list):
        for n in ast_node:
            n.full_source_code = src_code
            n.lineno = element.start_line
            n.end_lineno = element.end_line
            n.col_offset = element.start_column
            n.end_col_offset = element.end_column
    else:
        ast_node.full_source_code = src_code
        if hasattr(element, "start_line"):
            ast_node.lineno = element.start_line
            ast_node.end_lineno = element.end_line
            ast_node.col_offset = element.start_column
            ast_node.end_col_offset = element.end_column
    return ast_node


def filename_to_contract_name(fname: str) -> str:
    return "".join(
        [x.capitalize() for x in fname.split("/")[-1].split(".")[0].split("_")]
    )


def process_body(body, parent=None):
    # flatten list if necessary
    # wrap raw Call in Expr if needed
    new_body = []
    for f in body:
        if isinstance(f, list):
            for f2 in f:
                new_body.append(f2)
        elif isinstance(f, vy_nodes.List):
            for f2 in f.elements:
                if isinstance(f2, vy_nodes.Call):
                    expr_node = build_node(vy_nodes.Expr, value=f2)
                    new_body.append(expr_node)
                else:
                    new_body.append(f2)
        elif isinstance(f, vy_nodes.Call):
            expr_node = build_node(vy_nodes.Expr, value=f)
            new_body.append(expr_node)
        else:
            new_body.append(f)
    return new_body
