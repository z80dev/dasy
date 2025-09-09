from __future__ import annotations

from typing import List
import vyper.ast.nodes as n


def _join(parts: List[str], sep: str = ", ") -> str:
    return sep.join(p for p in parts if p is not None and p != "")


def vy_type_to_str(t: n.AST) -> str:
    """Pretty-print a Vyper type annotation from AST to Vyper source."""
    if isinstance(t, n.Name):
        return t.id
    if isinstance(t, n.Subscript):
        base = vy_type_to_str(t.value)
        sl = t.slice
        if hasattr(sl, "elts"):
            inner = _join([vy_expr_to_str(e) for e in sl.elts])
        elif hasattr(sl, "elements"):
            inner = _join([vy_expr_to_str(e) for e in sl.elements])
        else:
            inner = vy_expr_to_str(sl)
        return f"{base}[{inner}]"
    if isinstance(t, n.Attribute):
        return f"{vy_expr_to_str(t.value)}.{t.attr}"
    if isinstance(t, n.Tuple):
        items = getattr(t, "elts", None) or getattr(t, "elements", [])
        return f"({ _join([vy_type_to_str(e) for e in items]) })"
    # fallback
    return str(getattr(t, "id", getattr(t, "value", t)))


def vy_keyword_to_str(k: n.keyword) -> str:
    if k.arg is None:
        return vy_expr_to_str(k.value)
    return f"{k.arg}={vy_expr_to_str(k.value)}"


def vy_binop(op) -> str:
    return {
        n.Add: "+",
        n.Sub: "-",
        n.Mult: "*",
        n.Div: "/",
        n.FloorDiv: "//",
        n.Mod: "%",
        n.Pow: "**",
        n.BitAnd: "&",
        n.BitOr: "|",
        n.BitXor: "^",
        n.LShift: "<<",
        n.RShift: ">>",
    }.get(type(op), "?")


def vy_cmpop(op) -> str:
    m = {
        n.Eq: "==",
        n.NotEq: "!=",
        n.Lt: "<",
        n.LtE: "<=",
        n.Gt: ">",
        n.GtE: ">=",
    }
    if type(op) in m: return m[type(op)]
    t = type(op).__name__
    if t == "In": return "in"
    if t == "NotIn": return "not in"
    return "?"


def vy_unaryop(op) -> str:
    t = type(op).__name__
    if t == 'USub':
        return '-'
    if t == 'Not':
        return 'not'
    if t == 'UAdd':
        return '+'
    return '?'


def vy_expr_to_str(e: n.AST) -> str:
    if isinstance(e, n.Name):
        return e.id
    if isinstance(e, n.Attribute):
        return f"{vy_expr_to_str(e.value)}.{e.attr}"
    if isinstance(e, n.Str):
        # always double-quote to avoid confusing Hy reader
        s = e.value.replace("\\", "\\\\").replace("\"", "\\\"")
        return f'"{s}"'
    if isinstance(e, n.Bytes):
        # emit bytes as hex-escaped double-quoted literal to be safe for Hy reader
        b = e.value or b""
        hexed = ''.join(f"\\x{c:02x}" for c in b)
        return f' b"{hexed}"'.strip()
    if isinstance(e, n.Int):
        return str(e.value)
    if hasattr(n, "Hex") and isinstance(e, n.Hex):
        return e.value
    if isinstance(e, n.Tuple):
        items = getattr(e, "elts", None) or getattr(e, "elements", [])
        return "(" + _join([vy_expr_to_str(x) for x in items]) + ")"
    if isinstance(e, n.List):
        return "[" + _join([vy_expr_to_str(x) for x in e.elements]) + "]"
    if isinstance(e, n.Subscript):
        value = vy_expr_to_str(e.value)
        sl = e.slice
        if hasattr(sl, "elts"):
            inner = _join([vy_expr_to_str(x) for x in sl.elts])
        elif hasattr(sl, "elements"):
            inner = _join([vy_expr_to_str(x) for x in sl.elements])
        else:
            inner = vy_expr_to_str(sl)
        return f"{value}[{inner}]"
    if isinstance(e, n.Call):
        func = vy_expr_to_str(e.func)
        args = [vy_expr_to_str(a) for a in getattr(e, "args", [])]
        kwargs = [vy_keyword_to_str(k) for k in getattr(e, "keywords", [])]
        return f"{func}({ _join(args + kwargs) })"
    if hasattr(n, 'StaticCall') and isinstance(e, getattr(n, 'StaticCall')):
        return f"staticcall {vy_expr_to_str(e.value)}"
    if hasattr(n, 'ExtCall') and isinstance(e, getattr(n, 'ExtCall')):
        return f"extcall {vy_expr_to_str(e.value)}"
    if isinstance(e, n.BinOp):
        return f"({vy_expr_to_str(e.left)} {vy_binop(e.op)} {vy_expr_to_str(e.right)})"
    if isinstance(e, n.UnaryOp):
        _op = vy_unaryop(e.op)
        _expr = vy_expr_to_str(e.operand)
        return f'not {_expr}' if _op=='not' else f'{_op}{_expr}'
    if hasattr(n, 'IfExp') and isinstance(e, getattr(n, 'IfExp')):
        return f"({vy_expr_to_str(e.body)} if {vy_expr_to_str(e.test)} else {vy_expr_to_str(e.orelse)})"
    if isinstance(e, n.Compare):
        if hasattr(e, "op") and hasattr(e, "right"):
            return f"{vy_expr_to_str(e.left)} {vy_cmpop(e.op)} {vy_expr_to_str(e.right)}"
        if hasattr(e, "ops") and e.ops and e.comparators:
            return f"{vy_expr_to_str(e.left)} {vy_cmpop(e.ops[0])} {vy_expr_to_str(e.comparators[0])}"
    if hasattr(n, 'IfExp') and isinstance(e, getattr(n, 'IfExp')):
        return f'(if {dasy_expr_from_vy(e.test)} {dasy_expr_from_vy(e.body)} {dasy_expr_from_vy(e.orelse)})'
    if isinstance(e, n.NameConstant):
        return "True" if e.value is True else ("False" if e.value is False else "None")
    # fallback
    return getattr(getattr(e, "id", None), "id", None) or str(e)


def dasy_kw(name: str) -> str:
    return ":" + name


def dasy_type_from_vy(t: n.AST) -> str:
    """Pretty-print a Vyper AST type into a Dasy type form."""
    if isinstance(t, n.Name):
        # built-ins become :type
        return dasy_kw(t.id) if t.id and t.id[0].islower() else t.id
    if isinstance(t, n.Subscript):
        base = t.value
        if isinstance(base, n.Name) and base.id in ("String", "Bytes"):
            return f"({base.id.lower()} {vy_expr_to_str(t.slice)})"
        if isinstance(base, n.Name) and base.id == "DynArray":
            if hasattr(t.slice, "elts") and len(t.slice.elts) == 2:
                a, b = t.slice.elts
                return f"(dyn-array {dasy_type_from_vy(a)} {vy_expr_to_str(b)})"
            if hasattr(t.slice, "elements") and len(t.slice.elements) == 2:
                a, b = t.slice.elements
                return f"(dyn-array {dasy_type_from_vy(a)} {vy_expr_to_str(b)})"
        if isinstance(base, n.Name) and base.id == "HashMap":
            if hasattr(t.slice, "elts") and len(t.slice.elts) == 2:
                a, b = t.slice.elts
                return f"(hash-map {dasy_type_from_vy(a)} {dasy_type_from_vy(b)})"
            if hasattr(t.slice, "elements") and len(t.slice.elements) == 2:
                a, b = t.slice.elements
                return f"(hash-map {dasy_type_from_vy(a)} {dasy_type_from_vy(b)})"
        # fallback to raw
        return f"{dasy_type_from_vy(base)}[{vy_expr_to_str(t.slice)}]"
    if isinstance(t, n.Attribute):
        return f"{dasy_type_from_vy(t.value)}/{t.attr}"
    if isinstance(t, n.Tuple):
        return "'(" + _join([dasy_type_from_vy(e) for e in t.elts]) + ")"
    return ":unknown"


def dasy_expr_from_vy(e: n.AST) -> str:
    if isinstance(e, n.Name):
        return e.id
    if isinstance(e, n.Attribute):
        # self.owner -> self/owner
        if isinstance(e.value, n.Name) and e.value.id == "self":
            return f"self/{e.attr}"
        return f"(. {dasy_expr_from_vy(e.value)} {e.attr})"
    if isinstance(e, n.Str):
        s = e.value.replace("\\", "\\\\").replace("\"", "\\\"")
        return f'"{s}"'
    if isinstance(e, n.Bytes):
        b = e.value or b""
        hexed = ''.join(f"\\x{c:02x}" for c in b)
        return f'b"{hexed}"'
    if isinstance(e, n.Int):
        return str(e.value)
    if hasattr(n, "Hex") and isinstance(e, n.Hex):
        return e.value
    if isinstance(e, n.Tuple):
        items = getattr(e, "elts", None) or getattr(e, "elements", [])
        return "'(" + _join([dasy_expr_from_vy(x) for x in items]) + ")"
    if isinstance(e, n.List):
        return "[" + _join([dasy_expr_from_vy(x) for x in e.elements]) + "]"
    if isinstance(e, n.Subscript):
        value = dasy_expr_from_vy(e.value)
        sl = e.slice
        if hasattr(sl, "elts"):
            inner = _join([dasy_expr_from_vy(x) for x in sl.elts])
        else:
            inner = dasy_expr_from_vy(sl)
        return f"(subscript {value} {inner})"
    if isinstance(e, n.Call):
        # attribute call: obj.method(args) => (. obj method args)
        if isinstance(e.func, n.Attribute):
            obj = dasy_expr_from_vy(e.func.value)
            meth = e.func.attr
            args = [dasy_expr_from_vy(a) for a in getattr(e, "args", [])]
            kwargs = []
            for k in getattr(e, "keywords", []):
                if k.arg is None:
                    kwargs.append(dasy_expr_from_vy(k.value))
                else:
                    kwargs.append(f"{dasy_kw(k.arg)} {dasy_expr_from_vy(k.value)}")
            items = _join(args + kwargs, sep=" ")
            return f"(. {obj} {meth} {items})".strip()
        # plain call: f(args) => (f args)
        func = dasy_expr_from_vy(e.func)
        args = [dasy_expr_from_vy(a) for a in getattr(e, "args", [])]
        kwargs = []
        for k in getattr(e, "keywords", []):
            if k.arg is None:
                kwargs.append(dasy_expr_from_vy(k.value))
            else:
                kwargs.append(f"{dasy_kw(k.arg)} {dasy_expr_from_vy(k.value)}")
        items = _join(args + kwargs, sep=" ")
        return f"({func} {items})".strip()
    if isinstance(e, n.BinOp):
        op = vy_binop(e.op)
        return f"({op} {dasy_expr_from_vy(e.left)} {dasy_expr_from_vy(e.right)})"
    if isinstance(e, n.UnaryOp):
        op = vy_unaryop(e.op)
        if op in ("+", "-"):
            return f"({('u' if op=='-' else '')}sub {dasy_expr_from_vy(e.operand)})" if op == '-' else f"(+ {dasy_expr_from_vy(e.operand)})"
        return f"({op} {dasy_expr_from_vy(e.operand)})"
    if hasattr(n, 'IfExp') and isinstance(e, getattr(n, 'IfExp')):
        return f"({vy_expr_to_str(e.body)} if {vy_expr_to_str(e.test)} else {vy_expr_to_str(e.orelse)})"
    if isinstance(e, n.Compare):
        if hasattr(e, "op") and hasattr(e, "right"):
            op = vy_cmpop(e.op)
            return f"({op} {dasy_expr_from_vy(e.left)} {dasy_expr_from_vy(e.right)})"
        if hasattr(e, "ops") and e.ops and e.comparators:
            op = vy_cmpop(e.ops[0])
            return f"({op} {dasy_expr_from_vy(e.left)} {dasy_expr_from_vy(e.comparators[0])})"
    if hasattr(n, 'IfExp') and isinstance(e, getattr(n, 'IfExp')):
        return f'(if {dasy_expr_from_vy(e.test)} {dasy_expr_from_vy(e.body)} {dasy_expr_from_vy(e.orelse)})'
    if isinstance(e, n.NameConstant):
        return "True" if e.value is True else ("False" if e.value is False else "None")
    return f"(vyper {repr(vy_expr_to_str(e))})"
