from dasy import compiler
import sys

def main():

    src = ""

    for line in sys.stdin:
        src += line

    data = compiler.compile(src)
    print("0x" + data.bytecode.hex())


if __name__ == "__main__":
    main()
