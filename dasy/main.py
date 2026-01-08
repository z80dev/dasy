from dasy import compiler
from vyper.compiler import OUTPUT_FORMATS as VYPER_OUTPUT_FORMATS
import argparse
import sys
import logging
import difflib
from importlib.metadata import version as pkg_version, PackageNotFoundError

from dasy.parser.output import get_external_interface
from dasy.exceptions import DasyUsageError


def get_expanded_forms(src: str, filepath: str = None):
    """Return macro-expanded forms as a formatted string (for debugging/inspection)."""
    from dasy.parser.reader import read_many as dasy_read_many
    from dasy.parser.expander import expand_module
    from dasy.parser.context import ParseContext
    from dasy.parser import macros2
    from dasy.macro.syntax import MacroEnv

    # Create context
    context = ParseContext(source_path=filepath, source_code=src)

    # Read raw forms
    forms = list(dasy_read_many(src))

    # Macro expansion pass
    env = MacroEnv()
    macros2.install_builtin_dasy_macros(env)
    expanded = expand_module(forms, env, macros2.parse_define_syntax, context)

    # Pretty-print each expanded form
    def pretty(form, indent=0):
        """Simple pretty-printer for Hy models."""
        from hy import models

        sp = "  " * indent
        if isinstance(form, models.Expression):
            if len(form) == 0:
                return "()"
            parts = [pretty(x, indent + 1) for x in form]
            # If short enough, keep on one line
            one_line = "(" + " ".join(parts) + ")"
            if len(one_line) < 60:
                return one_line
            # Otherwise multiline
            inner = "\n".join("  " * (indent + 1) + p for p in parts)
            return "(\n" + inner + ")"
        elif isinstance(form, models.List):
            if len(form) == 0:
                return "[]"
            parts = [pretty(x, indent + 1) for x in form]
            return "[" + " ".join(parts) + "]"
        elif isinstance(form, models.String):
            return '"' + str(form).replace("\\", "\\\\").replace('"', '\\"') + '"'
        elif isinstance(form, models.Keyword):
            return ":" + form.name
        elif isinstance(form, models.Symbol):
            return str(form)
        elif isinstance(form, models.Integer):
            return str(int(form))
        elif isinstance(form, models.Float):
            return str(float(form))
        elif isinstance(form, models.Bytes):
            return repr(bytes(form))
        else:
            # Fallback - try to get a clean representation
            if hasattr(form, "__int__"):
                return str(int(form))
            return repr(form)

    return "\n\n".join(pretty(f) for f in expanded)


format_help = """Format to print, one or more of:
bytecode (default) - Deployable bytecode
bytecode_runtime   - Bytecode at runtime
abi                - ABI in JSON format
abi_python         - ABI in python format
source_map         - Vyper source map
method_identifiers - Dictionary of method signature to method identifier
userdoc            - Natspec user documentation
devdoc             - Natspec developer documentation
combined_json      - All of the above format options combined as single JSON output
layout             - Storage layout of a Vyper contract
ast                - AST in JSON format
external_interface - External (Dasy) interface of a contract, used for outside contract calls
vyper_interface    - External (Vyper) interface of a contract, used for outside contract calls
opcodes            - List of opcodes as a string
opcodes_runtime    - List of runtime opcodes as a string
ir                 - Intermediate representation in list format
ir_json            - Intermediate representation in JSON format
hex-ir             - Output IR and assembly constants in hex instead of decimal
no-optimize        - Do not optimize (don't use this for production code)
expand             - Show macro-expanded forms (for debugging macros)
"""

OUTPUT_FORMATS = VYPER_OUTPUT_FORMATS.copy()

OUTPUT_FORMATS["vyper_interface"] = OUTPUT_FORMATS["external_interface"]
OUTPUT_FORMATS["external_interface"] = get_external_interface


def main():
    parser = argparse.ArgumentParser(
        prog="dasy",
        description="Lispy Smart Contract Language for the EVM",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("filename", type=str, nargs="?", default="")
    parser.add_argument(
        "-f", "--format", help=format_help, default="bytecode", dest="format"
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List available output formats and exit",
    )
    parser.add_argument(
        "--evm-version",
        type=str,
        default=None,
        help="Override EVM version (e.g., cancun, paris)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging (DEBUG)"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress logs (ERROR only)"
    )
    try:
        ver = pkg_version("dasy")
    except PackageNotFoundError:
        ver = "unknown"
    parser.add_argument("--version", action="version", version=f"dasy {ver}")

    src = ""

    args = parser.parse_args()

    # Configure logging based on verbosity flags
    level = logging.WARNING
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")

    # List formats and exit if requested
    if args.list_formats:
        all_formats = set(OUTPUT_FORMATS.keys()) | {"expand"}
        for key in sorted(all_formats):
            print(key)
        return

    # Read source code
    filepath = None
    if args.filename != "":
        filepath = args.filename
        with open(args.filename, "r") as f:
            src = f.read()
            # Allow CLI to override EVM version via pragma appended last (wins over earlier pragmas)
            if args.evm_version and not args.filename.endswith(".vy"):
                src = src + f"\n(pragma :evm-version {args.evm_version})\n"
    else:
        for line in sys.stdin:
            src += line
        if args.evm_version:
            src = src + f"\n(pragma :evm-version {args.evm_version})\n"

    # Handle "expand" format specially (doesn't need full compilation)
    if args.format == "expand":
        print(get_expanded_forms(src, filepath))
        return

    # Full compilation for other formats
    if filepath and filepath.endswith(".vy"):
        data = compiler.CompilerData(
            src, contract_name=filepath.split("/")[-1].split(".")[0]
        )
    elif filepath:
        # Pass the filepath so macros like include! resolve relative paths correctly
        data = compiler.compile(src, name=filepath.split(".")[0], filepath=filepath)
    else:
        data = compiler.compile(src, name="StdIn")

    translate_map = {
        "abi_python": "abi",
        "json": "abi",
        "ast": "ast_dict",
        "ir_json": "ir_dict",
        "interface": "external_interface",
    }
    # Accept aliases and canonical names at input
    valid_inputs = set(OUTPUT_FORMATS.keys()) | set(translate_map.keys()) | {"expand"}
    output_format = translate_map.get(args.format, args.format)
    if output_format in OUTPUT_FORMATS:
        print(OUTPUT_FORMATS[output_format](data))
    else:
        # Provide helpful suggestions
        suggestions = difflib.get_close_matches(args.format, list(valid_inputs), n=3)
        msg = (
            f"Unrecognized output format '{args.format}'.\n"
            f"Valid options: {', '.join(sorted(valid_inputs))}."
        )
        if suggestions:
            msg += f"\nDid you mean: {', '.join(suggestions)}?"
        raise DasyUsageError(msg)


if __name__ == "__main__":
    main()
