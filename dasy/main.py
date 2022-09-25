from dasy import compiler, parser
from vyper.compiler import OUTPUT_FORMATS as VYPER_OUTPUT_FORMATS
from vyper import compiler as vyper_compiler
import argparse
import sys

from dasy.parser.output import generate_external_interface_output

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
"""

OUTPUT_FORMATS = VYPER_OUTPUT_FORMATS.copy()

OUTPUT_FORMATS["vyper_interface"] = OUTPUT_FORMATS["external_interface"]
OUTPUT_FORMATS["external_interface"] = generate_external_interface_output

def main():
    parser = argparse.ArgumentParser(
        prog="dasy",
        description="Lispy Smart Contract Language for the EVM",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("filename", type=str, nargs="?", default="")
    parser.add_argument("-f", help=format_help, default="bytecode", dest="format")

    src = ""

    args = parser.parse_args()

    if args.filename != "":
        with open(args.filename, "r") as f:
            src = f.read()
            data = compiler.compile(src, name=args.filename.split(".")[0])
    else:
        for line in sys.stdin:
            src += line
        data = compiler.compile(src, name="StdIn")

    translate_map = {"abi_python": "abi", "json": "abi", "ast": "ast_dict", "ir_json": "ir_dict", "interface": "external_interface"}
    output_format = translate_map.get(args.format, args.format)
    if output_format in OUTPUT_FORMATS:
        print(OUTPUT_FORMATS[output_format](data))
    else:
        raise Exception(
            f"Unrecognized Output Format {args.format}. Must be one of {OUTPUT_FORMATS.keys()}"
        )


if __name__ == "__main__":
    main()
