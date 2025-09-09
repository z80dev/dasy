from __future__ import annotations

import argparse
from typing import List

import vyper.ast.nodes as n

from dasy.parser.parse import parse_src
from .emit_common import vy_expr_to_str, vy_type_to_str, _join


def emit_stmt(s: n.AST, indent: int = 0) -> List[str]:
    pad = " " * indent
    out: List[str] = []
    if isinstance(s, n.Return):
        out.append(f"{pad}return {vy_expr_to_str(s.value)}")
    elif isinstance(s, n.Pass):
        out.append(f"{pad}pass")
    elif isinstance(s, n.Assert):
        msg = f", {vy_expr_to_str(s.msg)}" if getattr(s, "msg", None) else ""
        out.append(f"{pad}assert {vy_expr_to_str(s.test)}{msg}")
    elif isinstance(s, n.Log):
        # log Event(args...)
        out.append(f"{pad}log {vy_expr_to_str(s.value)}")
    elif hasattr(n, "Raise") and isinstance(s, getattr(n, "Raise")):
        # raise with message/exception
        exc = getattr(s, "exc", None)
        if exc is not None:
            out.append(f"{pad}raise {vy_expr_to_str(exc)}")
        else:
            out.append(f"{pad}raise")
    elif isinstance(s, n.Break):
        out.append(f"{pad}break")
    elif isinstance(s, n.Continue):
        out.append(f"{pad}continue")
    elif isinstance(s, n.Assign):
        tgt = s.target
        if isinstance(tgt, n.Attribute):
            left = f"{vy_expr_to_str(tgt.value)}.{tgt.attr}"
        else:
            left = vy_expr_to_str(tgt)
        out.append(f"{pad}{left} = {vy_expr_to_str(s.value)}")
    elif isinstance(s, n.AugAssign):
        left = vy_expr_to_str(s.target)
        from .emit_common import vy_binop

        out.append(f"{pad}{left} {vy_binop(s.op)}= {vy_expr_to_str(s.value)}")
    elif isinstance(s, n.AnnAssign):
        target = s.target
        name = getattr(target, "id", None) or vy_expr_to_str(target)
        typ = vy_type_to_str(s.annotation) if s.annotation else None
        rhs = f" = {vy_expr_to_str(s.value)}" if getattr(s, "value", None) is not None else ""
        if typ is None:
            out.append(f"{pad}{name}{rhs}")
        else:
            out.append(f"{pad}{name}: {typ}{rhs}")
    elif isinstance(s, n.Expr):
        out.append(f"{pad}{vy_expr_to_str(s.value)}")
    elif isinstance(s, n.If):
        out.append(f"{pad}if {vy_expr_to_str(s.test)}:")
        for b in s.body:
            out.extend(emit_stmt(b, indent + 4))
        if s.orelse:
            out.append(f"{pad}else:")
            for b in s.orelse:
                out.extend(emit_stmt(b, indent + 4))
    elif isinstance(s, n.For):
        # for i: <type> in iter:
        tgt = s.target
        name = None
        typ = None
        if isinstance(tgt, n.AnnAssign):
            name = getattr(tgt.target, "id", None) or vy_expr_to_str(tgt.target)
            typ = vy_type_to_str(tgt.annotation) if tgt.annotation else None
        else:
            ann = getattr(tgt, "annotation", None)
            if ann is not None and hasattr(tgt, "arg"):
                name = tgt.arg
                typ = vy_type_to_str(ann)
            else:
                name = vy_expr_to_str(tgt)
        if typ is None:
            typ = "int128"
        out.append(f"{pad}for {name}: {typ} in {vy_expr_to_str(s.iter)}:")
        for b in s.body:
            out.extend(emit_stmt(b, indent + 4))
    else:
        out.append(f"{pad}# TODO: unhandled stmt {type(s).__name__}")
    return out


def emit_module_vyper(mod: n.Module) -> str:
    lines: List[str] = []
    # Pragma (EVM version)
    evm_version = getattr(getattr(mod, "settings", None), "evm_version", None)
    if evm_version:
        lines.append(f"#pragma evm-version {evm_version}")
        lines.append("")
    # Events first
    for node in mod.body:
        if isinstance(node, n.EventDef):
            lines.append(f"event {node.name}:")
            for it in node.body:
                if isinstance(it, n.AnnAssign):
                    fname = getattr(it.target, "id", None) or vy_expr_to_str(it.target)
                    ann = it.annotation
                    if isinstance(ann, n.Call) and isinstance(ann.func, n.Name) and ann.func.id == "indexed":
                        # indexed(type)
                        a0 = ann.args[0] if getattr(ann, "args", []) else None
                        t = vy_type_to_str(a0) if a0 is not None else "unknown"
                        lines.append(f"    {fname}: indexed({t})")
                    else:
                        t = vy_type_to_str(ann)
                        lines.append(f"    {fname}: {t}")

    # Interfaces
    for node in mod.body:
        if hasattr(n, 'InterfaceDef') and isinstance(node, getattr(n, 'InterfaceDef')):
            lines.append(f"interface {node.name}:")
            for fn in node.body:
                # args
                args = []
                for a in fn.args.args:
                    ann = vy_type_to_str(a.annotation) if a.annotation else ''
                    args.append(f"{a.arg}: {ann}" if ann else a.arg)
                ret = vy_type_to_str(fn.returns) if fn.returns else None
                sig = f"    def {fn.name}({ _join(args) })"
                if ret:
                    sig += f" -> {ret}"
                sig += ":"
                # mark view/pure/payable as trailing annotation
                decs = [getattr(d, 'id', '') for d in getattr(fn, 'decorator_list', [])]
                vis = None
                if not decs and getattr(fn, 'body', None):
                    first = fn.body[0]
                    vis = getattr(getattr(first, 'value', None), 'id', None)
                if 'view' in decs or vis == 'view':
                    sig += " view"
                elif 'payable' in decs or vis == 'payable':
                    sig += " payable"
                else:
                    sig += " nonpayable"
                lines.append(sig)
            lines.append("")
    # Structs
    for node in mod.body:
        if hasattr(n, 'StructDef') and isinstance(node, getattr(n, 'StructDef')):
            lines.append(f"struct {node.name}:")
            for it in node.body:
                if isinstance(it, n.AnnAssign):
                    fname = getattr(it.target, 'id', None) or vy_expr_to_str(it.target)
                    t = vy_type_to_str(it.annotation)
                    lines.append(f"    {fname}: {t}")
            lines.append("")
    # Flags
    for node in mod.body:
        if hasattr(n, 'FlagDef') and isinstance(node, getattr(n, 'FlagDef')):
            lines.append(f"flag {node.name}:")
            for it in node.body:
                # Each item is an Expr with a Name value
                val = getattr(it, 'value', None)
                if isinstance(val, n.Name):
                    lines.append(f"    {val.id}")
            lines.append("")
            lines.append("")
    # State vars first
    for node in mod.body:
        if isinstance(node, n.VariableDecl):
            typ = vy_type_to_str(node.annotation)
            # Wrap visibility if flags present
            if getattr(node, "is_public", False):
                typ = f"public({typ})"
            if getattr(node, "is_immutable", False):
                typ = f"immutable({typ})"
            if getattr(node, "is_transient", False):
                typ = f"transient({typ})"
            line = f"{node.target.id}: {typ}"
            if getattr(node, "value", None) is not None:
                line += f" = {vy_expr_to_str(node.value)}"
            lines.append(line)
    if lines:
        lines.append("")

    for node in mod.body:
        if isinstance(node, n.FunctionDef):
            # decorators
            decs = [getattr(d, "id", "") for d in node.decorator_list]
            for d in decs:
                lines.append(f"@{d}")
            # signature
            arg_specs = []
            for a in node.args.args:
                ann = vy_type_to_str(a.annotation) if a.annotation else ""
                if ann:
                    arg_specs.append(f"{a.arg}: {ann}")
                else:
                    arg_specs.append(a.arg)
            ret = vy_type_to_str(node.returns) if node.returns else None
            sig = f"def {node.name}({ _join(arg_specs) })"
            if ret:
                sig += f" -> {ret}"
            sig += ":"
            lines.append(sig)
            if not node.body:
                lines.append("    pass")
            else:
                for st in node.body:
                    lines.extend(emit_stmt(st, 4))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    p = argparse.ArgumentParser(description="Convert Dasy source to Vyper source (best-effort)")
    p.add_argument("filename", nargs="?", help=".dasy file to convert (reads stdin if omitted)")
    p.add_argument("--check", action="store_true", help="Compile the generated Vyper to verify correctness")
    args = p.parse_args()
    if args.filename:
        with open(args.filename, "r") as f:
            src = f.read()
        mod, _ = parse_src(src, filepath=args.filename)
    else:
        import sys

        src = sys.stdin.read()
        mod, _ = parse_src(src)
    out = emit_module_vyper(mod)
    if args.check:
        # Verify by compiling with Vyper
        try:
            from vyper.compiler.input_bundle import FileInput
            from vyper.compiler.phases import CompilerData
            from vyper.compiler.settings import Settings
            from pathlib import Path
            p = Path("converted.vy")
            fi = FileInput(contents=out, source_id=0, path=p, resolved_path=p)
            cd = CompilerData(fi, settings=Settings())
            _ = cd.bytecode
        except Exception as e:
            import sys
            sys.stderr.write(f"Conversion produced non-compiling Vyper: {e}\n")
            raise
    print(out)


if __name__ == "__main__":
    main()
