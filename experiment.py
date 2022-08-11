from rich import print
import boa
import dasy

with open("hello_world.dasy", "r") as f:
    src = f.read()

compilation_data = dasy.compile(src)
contract = boa.contract.VyperContract(compilation_data)
print(f"calling addUints(10, 20): {contract.addUints(10, 20)}")
print(f"calling subUints(100, 20): {contract.subUints(100, 20)}")
