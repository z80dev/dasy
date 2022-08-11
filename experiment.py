from rich import print, inspect
import boa
import dasy
from vyper.compiler import phases

with open("hello_world.vy", "r") as f:
    src = f.read()

ast = phases.generate_ast(src, 0, "")
inspect(ast.body[2].body[0])
# compilation_data = dasy.compile(src)
# contract = boa.contract.VyperContract(compilation_data)
# print(f"calling addUints(10, 20): {contract.addUints(10, 20)}")
# print(f"calling subUints(100, 20): {contract.subUints(100, 20)}")
