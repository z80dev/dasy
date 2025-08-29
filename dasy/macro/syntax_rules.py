from __future__ import annotations

from typing import Any

from hy import models

from .syntax import Syntax


ELLIPSIS = models.Symbol("...")


def _is_expr(x: Any) -> bool:
    return isinstance(x, models.Expression)


def _is_list(x: Any) -> bool:
    return isinstance(x, models.List)


def _to_syntax(x: Any, scopes) -> Syntax:
    return Syntax(x, scopes)


def match(pattern, stx: Syntax, literals: set[str], scopes, binds=None):
    """Return env dict or None.

    Supports matching expressions and lists, with ellipses and identifier literals.
    """
    if binds is None:
        binds = {}
    p = pattern
    d = stx.datum

    # identifier literal or variable
    if isinstance(p, models.Symbol):
        ps = str(p)
        if ps in literals:
            return binds if (isinstance(d, models.Symbol) and str(d) == ps) else None
        # variable bind (matches any datum)
        binds.setdefault(ps, []).append(_to_syntax(d, stx.scopes))
        return binds

    # helper to match sequences with backtracking for ellipses
    def _match_seq(p_seq, d_seq, i, j, binds_local):
        # reached end of pattern
        if i >= len(p_seq):
            return binds_local if j == len(d_seq) else None
        # ellipsis case on next element
        if i + 1 < len(p_seq) and p_seq[i + 1] == ELLIPSIS:
            subpat = p_seq[i]
            # Try greedily from the end to reduce backtracking
            for k in range(len(d_seq), j - 1, -1):
                trial = {k2: v.copy() for k2, v in binds_local.items()}
                ok = True
                jj = j
                while jj < k:
                    r = match(subpat, Syntax(d_seq[jj], stx.scopes), literals, scopes, trial)
                    if r is None:
                        ok = False
                        break
                    jj += 1
                if not ok:
                    continue
                res = _match_seq(p_seq, d_seq, i + 2, jj, trial)
                if res is not None:
                    return res
            return None
        # regular element
        if j >= len(d_seq):
            return None
        trial = {k2: v.copy() for k2, v in binds_local.items()}
        r = match(p_seq[i], Syntax(d_seq[j], stx.scopes), literals, scopes, trial)
        if r is None:
            return None
        return _match_seq(p_seq, d_seq, i + 1, j + 1, trial)

    # sequence patterns (Expression or List)
    if (_is_expr(p) and _is_expr(d)) or (_is_list(p) and _is_list(d)):
        p_seq = list(p)
        d_seq = list(d)
        return _match_seq(p_seq, d_seq, 0, 0, binds)

    # atoms must be equal
    return binds if p == d else None


def substitute(template, binds, scopes):
    # symbol variable substitution
    if isinstance(template, models.Symbol):
        name = str(template)
        if name in binds:
            vals = binds[name]
            # last occurrence wins for 1:1
            return vals[-1].datum if len(vals) == 1 else models.Expression([v.datum for v in vals])
        return template

    # expression splice with ellipses
    if isinstance(template, models.Expression):
        out = []
        i = 0
        while i < len(template):
            if i + 1 < len(template) and template[i + 1] == ELLIPSIS:
                key = template[i]
                assert isinstance(key, models.Symbol), "ellipsis must follow a variable"
                seq = [v.datum for v in binds.get(str(key), [])]
                out.extend(seq)
                i += 2
            else:
                out.append(substitute(template[i], binds, scopes))
                i += 1
        return models.Expression(out)

    # list splice with ellipses
    if isinstance(template, models.List):
        out = []
        i = 0
        while i < len(template):
            if i + 1 < len(template) and template[i + 1] == ELLIPSIS:
                key = template[i]
                assert isinstance(key, models.Symbol), "ellipsis must follow a variable"
                seq = [v.datum for v in binds.get(str(key), [])]
                out.extend(seq)
                i += 2
            else:
                out.append(substitute(template[i], binds, scopes))
                i += 1
        return models.List(out)

    return template


class SyntaxRulesMacro:
    def __init__(self, literals, rules):
        self.literals = set(str(x) for x in literals)
        # each rule is (pattern_expr, template_expr)
        self.rules = rules

    def __call__(self, call_stx: Syntax, env):
        form = call_stx.datum
        scopes = call_stx.scopes
        head = None
        if isinstance(form, models.Expression) and len(form) > 0 and isinstance(form[0], models.Symbol):
            head = str(form[0])
        for (pat, tmpl) in self.rules:
            # Prefer matching with macro head stripped to avoid binding it as a variable
            p = pat
            d = form
            if (
                isinstance(pat, models.Expression)
                and len(pat) > 0
                and isinstance(pat[0], models.Symbol)
                and head is not None
                and str(pat[0]) == head
            ):
                p = models.Expression(list(pat[1:]))
                d = models.Expression(list(form[1:]))
            binds = match(p, Syntax(d, scopes), self.literals, scopes)
            # Fallback: if pattern/data are single nested expressions and no binds captured,
            # try matching inner expressions to support patterns like ((a op b)).
            if (
                binds is not None
                and isinstance(p, models.Expression)
                and isinstance(d, models.Expression)
                and len(p) == 1
                and len(d) == 1
                and isinstance(p[0], models.Expression)
                and isinstance(d[0], models.Expression)
                and (not binds or len(binds.keys()) == 0)
            ):
                nested = match(p[0], Syntax(d[0], scopes), self.literals, scopes)
                if nested is not None:
                    binds = nested
            if binds is not None:
                return substitute(tmpl, binds, scopes)
        raise Exception("no syntax-rules pattern matched")
