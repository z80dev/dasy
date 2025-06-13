from dasy.parser.utils import (
    process_body,
    add_src_map,
    set_parent_children,
    build_node,
    next_node_id_maker,
    pairwise,
    filename_to_contract_name,
    has_return,
)
from vyper.ast.nodes import Expr
import dasy


def test_filename_to_contract_name():
    filename = "test.vy"
    assert filename_to_contract_name(filename) == "Test"

    filename = "test_test.vy"
    assert filename_to_contract_name(filename) == "TestTest"


def test_next_nodeid():
    next_nodeid = next_node_id_maker()
    assert next_nodeid() == 0
    assert next_nodeid() == 1
    assert next_nodeid() == 2


def test_pairwise():
    assert list(pairwise([1, 2, 3, 4])) == [(1, 2), (3, 4)]


def test_has_return():
    assert has_return(dasy.read("(return 1)"))
    assert has_return(dasy.read("(return 1 2)"))
    assert has_return(dasy.read("(return)"))
    assert has_return(dasy.read("(return (return 1))"))
    assert not has_return(dasy.read("(1 2 3)"))


def test_build_node():
    node = build_node(Expr, value=1)
    node_id = node.node_id
    # Check attributes individually instead of comparing objects
    assert node.node_id == node_id
    assert node.ast_type == "Expr"
    assert node.value == 1


def test_set_parent_children():
    parent = build_node(Expr, value=1)
    child = build_node(Expr, value=2)
    set_parent_children(parent, [child])
    assert child._parent == parent
    assert parent._children == [child]


def test_add_src_map():
    src = "(1 2 3)"
    node = dasy.read(src)
    ast_node = build_node(Expr, value=1)
    ast_node = add_src_map(src, node, ast_node)
    assert ast_node.full_source_code == src
    assert ast_node.lineno == 1
    assert ast_node.end_lineno == 1
    assert ast_node.col_offset == 1
    assert ast_node.end_col_offset == 7


def test_process_body():
    body = [dasy.read("(1 2 3)"), dasy.read("(4 5 6)")]
    assert process_body(body) == [
        dasy.read("1"),
        dasy.read("2"),
        dasy.read("3"),
        dasy.read("4"),
        dasy.read("5"),
        dasy.read("6"),
    ]
