# for handling venom
from vyper.ir.s_expressions import parse_s_exp
from vyper.codegen.ir_node import IRnode
from vyper.builtin_functions import STMT_DISPATCH_TABLE, BuiltinFunction
from dasy.parser.utils import next_nodeid
from vyper.compiler import phases


def parse_venom(expr):
    ir = IRnode.from_list((parse_s_exp(expr[1]))[0])
    # generate some vyper code to patch in.
    IDENTIFIER = f"__DASY_VENOM_BUILTIN_{next_nodeid()}__"
    insert_code = f"{IDENTIFIER}()"

    # dynamically generate a class on the fly
    class generated_builtin(BuiltinFunction):
        _id = IDENTIFIER
        _inputs = ()
        _return_type = None

        def build_IR(self, expr, context):
            return ir

    STMT_DISPATCH_TABLE[IDENTIFIER] = generated_builtin()

    return phases.generate_ast(insert_code, 0, "").body[0]


def parse_vyper(expr):
    return phases.generate_ast(str(expr[1]), 0, "").body[0]
