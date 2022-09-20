import dasy
import hy

MACROS = ["cond"]


def is_macro(cmd_str):
    return cmd_str in MACROS


def handle_macro(expr):
    new_node = hy.macroexpand(expr)
    return dasy.parser.parse_node(new_node)


def parse_defmacro(expr):
    hy.eval(expr)
    MACROS.append(str(expr[1]))
    return None
