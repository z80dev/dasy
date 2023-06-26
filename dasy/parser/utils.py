from hy import models
import vyper.ast.nodes as vy_nodes
from .builtins import build_node


def add_src_map(src_code, element, ast_node):
    if ast_node is None:
        return None
    if isinstance(ast_node, list):
        for n in ast_node:
            add_src_map(src_code, element, n)
    else:
        ast_node.full_source_code = src_code
        if hasattr(element, "start_line"):
            ast_node.lineno = element.start_line
            ast_node.end_lineno = element.end_line
            ast_node.col_offset = element.start_column
            ast_node.end_col_offset = element.end_column
    return ast_node

def process_body(body):
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
