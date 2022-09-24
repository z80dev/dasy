from dasy import compiler
import argparse
import sys

format_help = """Format to print, one or more of:
bytecode (default) - Deployable bytecode
bytecode_runtime   - Bytecode at runtime
abi                - ABI in JSON format
layout             - Storage layout of a Dasy contract
ast                - AST in JSON format
interface          - Vyper interface of a contract
external_interface - External interface of a contract, used for outside contract calls
opcodes            - List of opcodes as a string
opcodes_runtime    - List of runtime opcodes as a string
ir                 - Intermediate representation in list format
"""


OUTPUT_HANDLERS = {
    "bytecode": lambda data: print("0x" + data.bytecode.hex()),
    "runtime_bytecode": lambda data: print(data.runtime_bytecode),
    "abi": lambda data: print(data.abi),
    "interface": lambda data: print(data.interface),
    "ir": lambda data: print(data.ir),
    "runtime_ir": lambda data: print(data.runtime_ir),
    "asm": lambda data: print(data.asm),
    "opcodes": lambda data: print(data.opcodes),
    "runtime_opcodes": lambda data: print(data.runtime_opcodes),
    "external_interface": lambda data: print(data.external_interface),
    "layout": lambda data: print(data.layout)
}

def main():
    parser = argparse.ArgumentParser(prog="dasy",
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
    else:
        for line in sys.stdin:
            src += line

    data = compiler.compile(src)
    if args.format in OUTPUT_HANDLERS:
        OUTPUT_HANDLERS[args.format](data)
    else:
        raise Exception(f"Unrecognized Output Format {args.format}. Must be one of {OUTPUT_HANDLERS.keys()}")


if __name__ == "__main__":
    main()
