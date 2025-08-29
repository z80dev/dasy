import dasy
import hy

MACROS = []


def is_macro(cmd_str):
    return cmd_str in MACROS


def macroexpand(code_str):
    return hy.macroexpand(hy.read(code_str))


def handle_macro(expr, context):
    # Make context available to macros through thread-local storage
    from .macro_context import set_macro_context, clear_macro_context
    
    set_macro_context(context)
    try:
        new_node = hy.macroexpand(expr)
        return dasy.parser.parse_node(new_node, context)
    finally:
        clear_macro_context()


def parse_defmacro(expr, context):
    hy.eval(expr)
    MACROS.append(str(expr[1]))
    return None
