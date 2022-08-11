from dasy import compiler
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(prog="dasy")
    parser.add_argument('filename', type=str, nargs='?', default="")

    src = ""

    args = parser.parse_args()

    if args.filename != "":
        with open(args.filename, 'r') as f:
            src = f.read()
    else:
        for line in sys.stdin:
            src += line

    data = compiler.compile(src)
    print("0x" + data.bytecode.hex())


if __name__ == "__main__":
    main()
