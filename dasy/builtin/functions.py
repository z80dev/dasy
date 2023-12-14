# for handling venom
from vyper.ast import Call, Expr
from vyper.ir.s_expressions import parse_s_exp
from vyper.codegen.ir_node import IRnode
from vyper.builtins.functions import (
    STMT_DISPATCH_TABLE,
    DISPATCH_TABLE,
    BuiltinFunction,
)
from vyper.compiler import phases

from dasy import parser
from dasy.parser.utils import get_ir_type

from hy import repr


def parse_ir(expr):
    # check for optional return type annotation as second element
    ret_type = None
    ir_expr = None
    if len(expr) == 3:
        ret_type = get_ir_type(expr[1].name)
        ir_expr = expr[2]
    elif len(expr) == 2:
        ir_expr = expr[1]
    ir = IRnode.from_list((parse_s_exp(repr(ir_expr)[1:]))[0], typ=ret_type)

    # generate some vyper code to patch in.
    IDENTIFIER = f"__DASY_VENOM_BUILTIN_{parser.next_nodeid()}__"
    insert_code = f"{IDENTIFIER}()"

    # dynamically generate a class on the fly
    class generated_builtin(BuiltinFunction):
        _id = IDENTIFIER
        _inputs = ()
        _return_type = ret_type

        def fetch_call_return(self, node):
            return self._return_type

        def infer_arg_types(self, node):
            return []

        def build_IR(self, expr, context):
            return ir

    if ret_type is not None:
        DISPATCH_TABLE[IDENTIFIER] = generated_builtin()
        gend_ast = phases.generate_ast(insert_code, 0, "")
        return gend_ast[1].body[0].value

    STMT_DISPATCH_TABLE[IDENTIFIER] = generated_builtin()
    return phases.generate_ast(insert_code, 0, "")[1].body[0]


def parse_vyper(expr):
    return phases.generate_ast(str(expr[1]), 0, "")[1].body[0]


def wrap_calls(nodes):
    new_nodes = []
    for call_node in nodes:
        if isinstance(call_node, Call):
            expr_node = parser.build_node(Expr, value=call_node)
            new_nodes.append(expr_node)
        else:
            new_nodes.append(call_node)
    return new_nodes


def parse_splice(expr):
    return_val = wrap_calls([parser.parse_node(n) for n in expr[1:]])
    return return_val
