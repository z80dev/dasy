import re
from pathlib import Path
from vyper.compiler import CompilerData
from vyper.semantics.types.function import FunctionVisibility

def convert_type(vyper_type: str) -> str:
    vyper_type = str(vyper_type)
    if "[" in vyper_type:
        base = re.search(r'[A-Za-z]+', vyper_type).group()
        size = re.search(r'\d+', vyper_type).group()
        if base in ["String", "Bytes"]:
            return f"({base.lower()} {size})"
        else:
            return f"(array {base.lower()} {size})"
    return f":{vyper_type}"

def generate_external_interface_output(compiler_data: CompilerData) -> str:
    interface = compiler_data.vyper_module_folded._metadata["type"]
    stem = Path(compiler_data.contract_name).stem
    # capitalize words separated by '_'
    # ex: test_interface.vy -> TestInterface
    contract_name = "".join([x.capitalize() for x in stem.split("_")]) if "_" in stem else str(stem)

    out = ";; External Interface\n"
    funcs = []
    for func in interface.members.values():
        if func.visibility == FunctionVisibility.INTERNAL or func.name == "__init__":
            continue
        args = ""
        cur_type = ""
        for name, typ in func.arguments.items():
            if str(typ) != cur_type:
                args += convert_type(typ) + " "
                cur_type = str(typ)
            args += f"{name} "
        args = "[" + args[:-1] + "]" # remove trailing space
        return_type = ""
        if func.return_type is not None:
            return_type = convert_type(func.return_type)
        mutability = func.mutability.value
        func_str = f"(defn {func.name} {args} {return_type} :{mutability})"
        funcs.append(func_str)
    body = "\n  ".join(funcs)
    out = f"{out}(definterface {contract_name}\n  {body})"
    return out
