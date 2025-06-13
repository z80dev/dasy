import re
from pathlib import Path
from vyper.compiler import CompilerData
from vyper.semantics.types.function import ContractFunctionT, FunctionVisibility


def convert_type(vyper_type: str) -> str:
    vyper_type = str(vyper_type)
    if "[" in vyper_type:
        base = re.search(r"[A-Za-z]+", vyper_type).group()
        size = re.search(r"\d+", vyper_type).group()
        if base in ["String", "Bytes"]:
            return f"({base.lower()} {size})"
        else:
            return f"(array {base.lower()} {size})"
    return f":{vyper_type}"


def get_external_interface(compiler_data: CompilerData) -> str:
    interface = compiler_data.annotated_vyper_module._metadata["type"]
    stem = Path(compiler_data.contract_path).stem
    # capitalize words separated by '_'
    # ex: test_interface.vy -> TestInterface
    contract_name = (
        "".join([x.capitalize() for x in stem.split("_")]) if "_" in stem else str(stem)
    )

    out = ";; External Interface\n"
    funcs = []
    for func in [
        func for func in interface.members.values() if type(func) == ContractFunctionT
    ]:
        if func.visibility == FunctionVisibility.INTERNAL or func.name == "__init__":
            continue
        args = ""
        cur_type = ""
        for arg in func.arguments:
            if str(arg.typ) != cur_type:
                args += convert_type(arg.typ) + " "
                cur_type = str(arg.typ)
            args += f"{arg.name} "
        args = "[" + args[:-1] + "]"  # remove trailing space
        return_type = ""
        if func.return_type is not None:
            return_type = convert_type(func.return_type)
        mutability = func.mutability.value
        func_str = f"(defn {func.name} {args} {return_type} :{mutability})"
        funcs.append(func_str)
    body = "\n  ".join(funcs)
    out = f"{out}(definterface {contract_name}\n  {body})"
    return out
