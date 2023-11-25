# for handling venom
from vyper.ast import Call, Expr
from vyper.ir.s_expressions import parse_s_exp
from vyper.codegen.ir_node import IRnode
from vyper.builtins.functions import STMT_DISPATCH_TABLE, BuiltinFunction
from vyper.compiler import phases

from dasy import parser


def parse_venom(expr):
    ir = IRnode.from_list((parse_s_exp(expr[1]))[0])
    # generate some vyper code to patch in.
    IDENTIFIER = f"__DASY_VENOM_BUILTIN_{parser.next_nodeid()}__"
    insert_code = f"{IDENTIFIER}()"

    # dynamically generate a class on the fly
    class generated_builtin(BuiltinFunction):
        _id = IDENTIFIER
        _inputs = ()
        _return_type = None

        def build_IR(self, expr, context):
            return ir

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
