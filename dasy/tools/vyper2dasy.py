from __future__ import annotations

import argparse
from typing import List

import vyper.ast as vast
import vyper.ast.nodes as n

from .emit_common import (
    dasy_expr_from_vy,
    dasy_type_from_vy,
)


def emit_stmt_dasy(s: n.AST, indent: int = 0) -> List[str]:
    pad = " " * indent
    out: List[str] = []
    if isinstance(s, n.Return):
        out.append(f"{pad}(return {dasy_expr_from_vy(s.value)})")
    elif isinstance(s, n.Pass):
        out.append(f"{pad}(pass)")
    elif isinstance(s, n.Assert):
        msg = f" {dasy_expr_from_vy(s.msg)}" if getattr(s, "msg", None) else ""
        out.append(f"{pad}(assert {dasy_expr_from_vy(s.test)}{msg})")
    elif isinstance(s, n.Log):
        out.append(f"{pad}(log {dasy_expr_from_vy(s.value)})")
    elif hasattr(n, "Raise") and isinstance(s, getattr(n, "Raise")):
        exc = getattr(s, "exc", None)
        if exc is not None:
            out.append(f"{pad}(raise {dasy_expr_from_vy(exc)})")
        else:
            out.append(f"{pad}(raise)")
    elif isinstance(s, n.Break):
        out.append(f"{pad}(break)")
    elif isinstance(s, n.Continue):
        out.append(f"{pad}(continue)")
    elif isinstance(s, n.AnnAssign):
        name = getattr(s.target, "id", None) or dasy_expr_from_vy(s.target)
        typ = dasy_type_from_vy(s.annotation) if s.annotation is not None else ":any"
        if getattr(s, "value", None) is not None:
            out.append(f"{pad}(defvar {name} {typ} {dasy_expr_from_vy(s.value)})")
        else:
            out.append(f"{pad}(defvar {name} {typ})")
    elif isinstance(s, n.Assign):
        tgt = s.target
        if (
            isinstance(tgt, n.Attribute)
            and isinstance(tgt.value, n.Name)
            and tgt.value.id == "self"
        ):
            left = f"self/{tgt.attr}"
        else:
            left = dasy_expr_from_vy(tgt)
        out.append(f"{pad}(set {left} {dasy_expr_from_vy(s.value)})")
    elif isinstance(s, n.AugAssign):
        # Convert to explicit set using op
        from .emit_common import vy_binop

        op = vy_binop(s.op)
        out.append(
            f"{pad}(set {dasy_expr_from_vy(s.target)} ({op} {dasy_expr_from_vy(s.target)} {dasy_expr_from_vy(s.value)}))"
        )
    elif isinstance(s, n.Expr):
        out.append(f"{pad}{dasy_expr_from_vy(s.value)}")
    elif isinstance(s, n.If):
        out.append(f"{pad}(if {dasy_expr_from_vy(s.test)}")
        # body
        if s.body:
            for i, b in enumerate(s.body):
                out.extend(emit_stmt_dasy(b, indent + 2))
        else:
            out.append(" " * (indent + 2) + "(pass)")
        # orelse
        if s.orelse:
            out.append(f"{pad} " + "(do")
            for b in s.orelse:
                out.extend(emit_stmt_dasy(b, indent + 2))
            out.append(f"{pad} )")
        out.append(f"{pad})")
    elif isinstance(s, n.For):
        # Extract typed target - can be arg node, AnnAssign, or Name
        target = s.target
        name = None
        typ = None
        # Check for arg node (has .arg attribute for name)
        if hasattr(target, "arg") and target.arg:
            name = target.arg
            typ = getattr(target, "annotation", None)
        # Check for AnnAssign (has .target with name)
        elif isinstance(target, n.AnnAssign):
            name = getattr(target.target, "id", None) or dasy_expr_from_vy(
                target.target
            )
            typ = target.annotation
        # Check for Name node
        elif isinstance(target, n.Name):
            name = target.id
        # Fallback
        if name is None:
            name = getattr(target, "id", None) or "i"
        typ_s = dasy_type_from_vy(typ) if typ is not None else "uint256"
        out.append(f"{pad}(for [{name} {typ_s} {dasy_expr_from_vy(s.iter)}]")
        for b in s.body:
            out.extend(emit_stmt_dasy(b, indent + 2))
        out.append(f"{pad})")
    else:
        out.append(f"{pad};; TODO: unhandled stmt {type(s).__name__}")
    return out


def emit_module_dasy(mod: n.Module) -> str:
    lines: List[str] = []
    # Events
    for node in mod.body:
        if isinstance(node, n.EventDef):
            lines.append(f"(defevent {node.name}")
            for it in node.body:
                if isinstance(it, n.AnnAssign):
                    fname = getattr(it.target, "id", None) or dasy_expr_from_vy(
                        it.target
                    )
                    ann = it.annotation
                    if (
                        isinstance(ann, n.Call)
                        and isinstance(ann.func, n.Name)
                        and ann.func.id == "indexed"
                    ):
                        # first arg is the type
                        arg0 = ann.args[0] if getattr(ann, "args", []) else None
                        t_s = (
                            dasy_type_from_vy(arg0) if arg0 is not None else ":unknown"
                        )
                        lines.append(f"  {fname} (indexed {t_s})")
                    else:
                        t_s = dasy_type_from_vy(ann)
                        lines.append(f"  {fname} {t_s}")
            lines.append(")\n")
    # Structs
    for node in mod.body:
        if hasattr(n, "StructDef") and isinstance(node, getattr(n, "StructDef")):
            lines.append(f"(defstruct {node.name}")
            for it in node.body:
                if isinstance(it, n.AnnAssign):
                    fname = getattr(it.target, "id", None) or dasy_expr_from_vy(
                        it.target
                    )
                    t_s = dasy_type_from_vy(it.annotation)
                    lines.append(f"  {fname} {t_s}")
            lines.append(")\n")
    # Flags
    for node in mod.body:
        if hasattr(n, "FlagDef") and isinstance(node, getattr(n, "FlagDef")):
            members = []
            for it in node.body:
                val = getattr(it, "value", None)
                if isinstance(val, n.Name):
                    members.append(val.id)
            lines.append(f"(defflag {node.name}")
            for m in members:
                lines.append(f"  {m}")
            lines.append(")\n")
    # Interfaces
    for node in mod.body:
        if hasattr(n, "InterfaceDef") and isinstance(node, getattr(n, "InterfaceDef")):
            lines.append(f"(definterface {node.name}")
            for fn in node.body:
                # args
                arg_parts = []
                for a in fn.args.args:
                    if a.annotation is not None:
                        arg_parts.append(f"[{a.arg} {dasy_type_from_vy(a.annotation)}]")
                    else:
                        arg_parts.append(a.arg)
                args_vec = "[" + " ".join(arg_parts) + "]"
                ret = dasy_type_from_vy(fn.returns) if fn.returns else None
                # visibility from decorators or body
                decs = [getattr(d, "id", "") for d in getattr(fn, "decorator_list", [])]
                vis = None
                if not decs and getattr(fn, "body", None):
                    first = fn.body[0]
                    vis = getattr(getattr(first, "value", None), "id", None)
                if "view" in decs or vis == "view":
                    vis = ":view"
                elif "pure" in decs or vis == "pure":
                    vis = ":pure"
                elif "payable" in decs or vis == "payable":
                    vis = ":payable"
                else:
                    vis = ":nonpayable"
                sig = f"  (defn {fn.name} {args_vec}"
                if ret:
                    sig += f" {ret}"
                sig += f" {vis})"
                lines.append(sig)
            lines.append(")\n")
    # State vars
    for node in mod.body:
        if isinstance(node, n.VariableDecl):
            typ = dasy_type_from_vy(node.annotation)
            if getattr(node, "is_public", False):
                typ = f"(public {typ})"
            if getattr(node, "is_immutable", False):
                typ = f"(immutable {typ})"
            if getattr(node, "is_transient", False):
                typ = f"(transient {typ})"
            if getattr(node, "value", None) is not None:
                lines.append(
                    f"(defvar {node.target.id} {typ} {dasy_expr_from_vy(node.value)})"
                )
            else:
                lines.append(f"(defvars {node.target.id} {typ})")
    if lines:
        lines.append("")

    for node in mod.body:
        if isinstance(node, n.FunctionDef):
            # decorators -> attributes
            attrs = []
            for d in node.decorator_list:
                if isinstance(d, n.Name) and d.id in {
                    "external",
                    "internal",
                    "view",
                    "pure",
                    "payable",
                    "nonreentrant",
                }:
                    attrs.append(f":{d.id}")
                elif isinstance(d, n.Name) and d.id == "deploy":
                    # constructor marker
                    pass
            # args vector pairs: [:type name ...]
            arg_parts = []
            for a in node.args.args:
                if a.annotation is not None:
                    arg_parts.append(dasy_type_from_vy(a.annotation))
                    arg_parts.append(a.arg)
                else:
                    # no type: keep name only
                    arg_parts.append(a.arg)
            args_vec = "[" + " ".join(arg_parts) + "]"
            # returns
            returns = dasy_type_from_vy(node.returns) if node.returns else None
            # header
            hdr = f"(defn {node.name} {args_vec}"
            if returns:
                hdr += f" {returns}"
            # Always include an attribute list to satisfy Dasy defn shape
            if attrs:
                hdr += f" [{ ' '.join(attrs) }]"
            else:
                hdr += " []"
            lines.append(hdr)
            # body
            if not node.body:
                lines.append("  (pass)")
                lines.append(")")
            else:
                for st in node.body:
                    lines.extend(emit_stmt_dasy(st, 2))
                lines.append(")")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    p = argparse.ArgumentParser(
        description="Convert Vyper source to Dasy source (best-effort)"
    )
    p.add_argument(
        "filename", nargs="?", help=".vy file to convert (reads stdin if omitted)"
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Compile the generated Dasy to verify correctness",
    )
    args = p.parse_args()
    if args.filename:
        with open(args.filename, "r") as f:
            src = f.read()
        mod = vast.parse_to_ast(src, source_id=0)
    else:
        import sys

        src = sys.stdin.read()
        mod = vast.parse_to_ast(src, source_id=0)
    out = emit_module_dasy(mod)
    # Preserve pragma if present in source
    import re

    m = re.search(r"pragma\s+evm-version\s+([A-Za-z0-9_\-]+)", src)
    if m:
        evm = m.group(1)
        out = f'(pragma :evm-version "{evm}")\n\n' + out
    if args.check:
        # Try compiling with Dasy compiler to ensure validity
        try:
            from dasy import compiler as dcompiler

            dcompiler.compile(out, name="Converted")
        except Exception as e:
            import sys

            sys.stderr.write(f"Conversion produced non-compiling Dasy: {e}\n")
            raise
    print(out)


if __name__ == "__main__":
    main()
