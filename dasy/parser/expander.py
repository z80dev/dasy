from __future__ import annotations

from hy import models

from ..macro.syntax import Syntax
from .macro_context import set_macro_context, clear_macro_context


def expand(form, env):
    # expand macro calls recursively; otherwise, walk into subforms
    if isinstance(form, models.Expression) and len(form) > 0:
        head = form[0]
        if isinstance(head, models.Symbol):
            name = str(head)
            # Avoid expanding inside certain Hy-first macros to keep shapes intact
            # (none currently)
            m = env.lookup(name)
            if m is not None:
                expanded = m(Syntax(form, ()), env)
                return expand(expanded, env)
        # otherwise recursively expand subforms
        return models.Expression([expand(x, env) for x in form])
    if isinstance(form, models.List):
        return models.List([expand(x, env) for x in form])
    return form


def _flatten_expanded(val, env):
    # If a macro returns a list of forms, expand each and flatten
    if isinstance(val, models.List):
        result = []
        for x in val:
            ex = expand(x, env)
            if isinstance(ex, models.List):
                result.extend(_flatten_expanded(ex, env))
            else:
                result.append(ex)
        return result
    return [val]


def expand_module(forms, env, parse_define_syntax_fn, context):
    out = []
    set_macro_context(context)
    try:
        for f in forms:
            if (
                isinstance(f, models.Expression)
                and len(f) > 0
                and isinstance(f[0], models.Symbol)
                and str(f[0]) == "define-syntax"
            ):
                parse_define_syntax_fn(f, context, env)
                continue
            expanded = expand(f, env)
            out.extend(_flatten_expanded(expanded, env))
    finally:
        clear_macro_context()
    return out
