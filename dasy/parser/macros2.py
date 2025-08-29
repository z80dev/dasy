from __future__ import annotations

from hy import models

from .context import ParseContext
from ..macro.syntax_rules import SyntaxRulesMacro, ELLIPSIS
from ..macro.syntax import Syntax
from .macro_context import get_macro_context
from .macro_utils import check_include_recursion, get_include_stack, compile_for_interface
from .reader import read_many as dasy_read_many
from .output import get_external_interface


def parse_define_syntax(expr: models.Expression, context: ParseContext, env) -> None:
    # (define-syntax NAME (syntax-rules (lit ...) ( (pat) tmpl ) ...))
    if len(expr) < 3:
        raise Exception("define-syntax requires a name and a specification")
    _, name, spec = expr
    if not (isinstance(spec, models.Expression) and str(spec[0]) == "syntax-rules"):
        raise Exception("Only syntax-rules is supported in define-syntax")

    literals = models.Expression([])
    start = 1
    if len(spec) > 1 and isinstance(spec[1], (models.Expression, models.List)):
        literals = spec[1]
        start = 2

    # normalize literals to expression elements sequence
    lits = []
    if isinstance(literals, models.Expression) or isinstance(literals, models.List):
        for el in literals:
            lits.append(el)
    else:
        lits = []

    rules = []
    for clause in spec[start:]:
        if not (isinstance(clause, models.Expression) and len(clause) == 2):
            raise Exception("syntax-rules clause must be a pair (pattern template)")
        pat, tmpl = clause
        rules.append((pat, tmpl))

    macro = SyntaxRulesMacro(lits, rules)
    env.define(str(name), macro)


def install_builtin_dasy_macros(env) -> None:
    """Register a small set of builtin Dasy macros (cond, doto, ->, ->>, when, unless, let)."""
    # Build with Hy model constructors to avoid string parsing

    def sym(s: str):
        return models.Symbol(s)

    def kw(s: str):
        return models.Keyword(s)

    def exp(*xs):
        return models.Expression(list(xs))

    def lst(*xs):
        return models.List(list(xs))

    # cond
    cond_rules = [
        # (cond :else e) => e
        (exp(sym("cond"), kw("else"), sym("e")), sym("e")),
        # (cond test expr) => (if test expr)
        (exp(sym("cond"), sym("test"), sym("expr")), exp(sym("if"), sym("test"), sym("expr"))),
        # (cond test expr :else e) => (if test expr e)
        (
            exp(sym("cond"), sym("test"), sym("expr"), kw("else"), sym("e")),
            exp(sym("if"), sym("test"), sym("expr"), sym("e")),
        ),
        # (cond test expr rest ...) => (if test expr (cond rest ...))
        (
            exp(sym("cond"), sym("test"), sym("expr"), sym("rest"), ELLIPSIS),
            exp(sym("if"), sym("test"), sym("expr"), exp(sym("cond"), sym("rest"), ELLIPSIS)),
        ),
    ]
    env.define("cond", SyntaxRulesMacro([kw("else")], cond_rules))

    # keep doto provided by Hy for now, due to reader/shape nuances

    # thread macros are provided here as Dasy-native procedural macros

    # when
    when_rules = [
        (exp(sym("when"), sym("test"), sym("body"), ELLIPSIS), exp(sym("if"), sym("test"), exp(sym("do"), sym("body"), ELLIPSIS))),
    ]
    env.define("when", SyntaxRulesMacro([], when_rules))

    # unless: expand to (if test None (do body ...))
    unless_rules = [
        (
            exp(sym("unless"), sym("test"), sym("body"), ELLIPSIS),
            exp(sym("if"), sym("test"), models.Symbol("None"), exp(sym("do"), sym("body"), ELLIPSIS)),
        )
    ]
    env.define("unless", SyntaxRulesMacro([], unless_rules))

    # let
    # (let [] body ...) => (do body ...)
    # (let [x v rest ...] body ...) => (do (defvar x v) (let [rest ...] body ...))
    let_rules = [
        (
            exp(sym("let"), lst(), sym("body"), ELLIPSIS),
            exp(sym("do"), sym("body"), ELLIPSIS),
        ),
        (
            exp(sym("let"), lst(sym("x"), sym("v"), sym("rest"), ELLIPSIS), sym("body"), ELLIPSIS),
            exp(
                sym("do"),
                exp(sym("defvar"), sym("x"), sym("v")),
                exp(sym("let"), lst(sym("rest"), ELLIPSIS), sym("body"), ELLIPSIS),
            ),
        ),
    ]
    env.define("let", SyntaxRulesMacro([], let_rules))

    # set-in: (set-in obj field new) => (set (. obj field) new)
    set_in_rules = [
        (
            exp(sym("set-in"), sym("obj"), sym("field"), sym("new")),
            exp(sym("set"), exp(sym("."), sym("obj"), sym("field")), sym("new")),
        )
    ]
    env.define("set-in", SyntaxRulesMacro([], set_in_rules))

    # get-at: nested subscription
    # (get-at obj key)              => (subscript obj key)
    # (get-at obj key rest ...)     => (get-at (subscript obj key) rest ...)
    get_at_rules = [
        (
            exp(sym("get-at"), sym("obj"), sym("key")),
            exp(sym("subscript"), sym("obj"), sym("key")),
        ),
        (
            exp(sym("get-at"), sym("obj"), sym("key"), sym("rest"), ELLIPSIS),
            exp(sym("get-at"), exp(sym("subscript"), sym("obj"), sym("key")), sym("rest"), ELLIPSIS),
        ),
    ]
    env.define("get-at", SyntaxRulesMacro([], get_at_rules))

    # get-at! : list-based path
    # (get-at! obj [])           => obj
    # (get-at! obj [k])          => (subscript obj k)
    # (get-at! obj [k rest ...]) => (get-at! (subscript obj k) [rest ...])
    get_at_bang_rules = [
        (
            exp(sym("get-at!"), sym("obj"), lst()),
            sym("obj"),
        ),
        (
            exp(sym("get-at!"), sym("obj"), lst(sym("k"))),
            exp(sym("subscript"), sym("obj"), sym("k")),
        ),
        (
            exp(sym("get-at!"), sym("obj"), lst(sym("k"), sym("rest"), ELLIPSIS)),
            exp(sym("get-at!"), exp(sym("subscript"), sym("obj"), sym("k")), lst(sym("rest"), ELLIPSIS)),
        ),
    ]
    env.define("get-at!", SyntaxRulesMacro([], get_at_bang_rules))

    # set-at: variadic keys, last is value
    # (set-at obj key value)             => (set (subscript obj key) value)
    # (set-at obj key rest ... value)    => (set-at (subscript obj key) rest ... value)
    set_at_rules = [
        (
            exp(sym("set-at"), sym("obj"), sym("key"), sym("value")),
            exp(sym("set"), exp(sym("subscript"), sym("obj"), sym("key")), sym("value")),
        ),
        (
            exp(sym("set-at"), sym("obj"), sym("key"), sym("rest"), ELLIPSIS, sym("value")),
            exp(sym("set-at"), exp(sym("subscript"), sym("obj"), sym("key")), sym("rest"), ELLIPSIS, sym("value")),
        ),
    ]
    env.define("set-at", SyntaxRulesMacro([], set_at_rules))

    # set-at! using list of keys
    # (set-at! obj keys val) => (set (get-at! obj keys) val)
    set_at_bang_rules = [
        (
            exp(sym("set-at!"), sym("obj"), sym("keys"), sym("val")),
            exp(sym("set"), exp(sym("get-at!"), sym("obj"), sym("keys")), sym("val")),
        )
    ]
    env.define("set-at!", SyntaxRulesMacro([], set_at_bang_rules))

    # thread-first (->) as a procedural macro for robustness
    def _thread_first(call_stx: Syntax, _env):
        form = call_stx.datum
        # form = (-> x s1 s2 ...)
        x = form[1]
        acc = x
        for step in form[2:]:
            if isinstance(step, models.Expression) and len(step) > 0:
                f = step[0]
                rest = list(step[1:])
                acc = models.Expression([f, acc, *rest])
            else:
                # bare symbol/function name
                acc = models.Expression([step, acc])
        return acc
    env.define("->", _thread_first)

    # thread-last (->>) as a procedural macro
    def _thread_last(call_stx: Syntax, _env):
        form = call_stx.datum
        x = form[1]
        acc = x
        for step in form[2:]:
            if isinstance(step, models.Expression) and len(step) > 0:
                f = step[0]
                rest = list(step[1:])
                acc = models.Expression([f, *rest, acc])
            else:
                acc = models.Expression([step, acc])
        return acc
    env.define("->>", _thread_last)

    # doto as procedural macro (returns a (do ...) of calls)
    def _doto(call_stx: Syntax, _env):
        form = call_stx.datum
        obj = form[1]
        calls = []
        for step in form[2:]:
            if isinstance(step, models.Expression):
                # Handle ((. None meth) a ...) -> (. obj meth a ...)
                if (
                    len(step) >= 1
                    and isinstance(step[0], models.Expression)
                    and len(step[0]) == 3
                    and isinstance(step[0][0], models.Symbol)
                    and str(step[0][0]) == "."
                    and isinstance(step[0][1], models.Symbol)
                    and str(step[0][1]) == "None"
                ):
                    meth = step[0][2]
                    args = list(step[1:])
                    call_expr = models.Expression([models.Symbol("."), obj, meth, *args])
                else:
                    f = step[0]
                    args = list(step[1:])
                    call_expr = models.Expression([f, obj, *args])
            else:
                # bare symbol
                call_expr = models.Expression([step, obj])
            calls.append(call_expr)
        return models.Expression([models.Symbol("do"), *calls])
    env.define("doto", _doto)

    # set-self: (set-self k1 k2 ...) => (do (set (. self k1) k1) (set (. self k2) k2) ...)
    def _set_self(call_stx: Syntax, _env):
        form = call_stx.datum
        assigns = []
        for k in form[1:]:
            assigns.append(
                models.Expression([
                    models.Symbol("set"),
                    models.Expression([models.Symbol("."), models.Symbol("self"), k]),
                    k,
                ])
            )
        return models.Expression([models.Symbol("do"), *assigns])
    env.define("set-self", _set_self)

    # include!: read another .dasy file and splice its forms
    def _include_bang(call_stx: Syntax, _env):
        form = call_stx.datum
        if len(form) != 2:
            raise Exception("include! requires exactly one filename argument")
        filename_node = form[1]
        if not isinstance(filename_node, models.String):
            raise Exception("include! filename must be a string literal")
        from pathlib import Path
        fname = str(filename_node)
        ctx = get_macro_context()
        base_dir = ctx.base_dir if ctx else Path.cwd()
        p = Path(fname)
        if p.is_absolute():
            path = p
        else:
            # If fname starts with the current base dir name (e.g. "examples/")
            # and base_dir already points to that folder, avoid duplicating it
            if p.parts and p.parts[0] == base_dir.name:
                path = base_dir.parent / p
            else:
                path = base_dir / p
        abs_path = str(path.absolute())
        # recursion guard
        check_include_recursion(str(path))
        include_stack = get_include_stack()
        include_stack.add(abs_path)
        try:
            with open(path, 'r') as f:
                src = f.read()
            forms = dasy_read_many(src, filename=str(path))
            return models.List(list(forms))
        finally:
            include_stack.discard(abs_path)
    env.define("include!", _include_bang)

    # interface!: compile target and read back interface as forms
    def _interface_bang(call_stx: Syntax, _env):
        form = call_stx.datum
        if len(form) != 2:
            raise Exception("interface! requires exactly one filename argument")
        filename_node = form[1]
        if not isinstance(filename_node, models.String):
            raise Exception("interface! filename must be a string literal")
        fname = str(filename_node)
        from pathlib import Path
        ctx = get_macro_context()
        base_dir = ctx.base_dir if ctx else Path.cwd()
        p = Path(fname)
        path = p if p.is_absolute() else (base_dir / p)
        data = compile_for_interface(str(path))
        interface_str = get_external_interface(data)
        forms = dasy_read_many(interface_str, filename=str(path))
        return models.List(list(forms))
    env.define("interface!", _interface_bang)

    # (no builtin infix; examples define their own)
