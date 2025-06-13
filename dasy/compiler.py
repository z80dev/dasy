from vyper.compiler.phases import CompilerData as VyperCompilerData
from pathlib import Path
from vyper.compiler.output import (
    build_abi_output,
    build_asm_output,
    build_bytecode_runtime_output,
    build_external_interface_output,
    build_interface_output,
    build_ir_output,
    build_ir_runtime_output,
    build_layout_output,
    build_opcodes_output,
)
from vyper.compiler.settings import Settings, anchor_settings
from dasy.parser import parse_src
from dasy.parser.utils import filename_to_contract_name


class CompilerData(VyperCompilerData):
    def __init__(self, *args, **kwargs):
        VyperCompilerData.__init__(self, *args, **kwargs)

    @property
    def runtime_bytecode(self):
        runtime_bytecode = build_bytecode_runtime_output(self)
        self.__dict__["runtime_bytecode"] = runtime_bytecode
        return runtime_bytecode

    @property
    def abi(self):
        abi = build_abi_output(self)
        self.__dict__["abi"] = abi
        return abi

    @property
    def interface(self):
        interface = build_interface_output(self)
        self.__dict__["interface"] = interface
        return interface

    @property
    def ir(self):
        ir = build_ir_output(self)
        self.__dict__["ir"] = ir
        return ir

    @property
    def runtime_ir(self):
        ir = build_ir_runtime_output(self)
        self.__dict__["runtime_ir"] = ir
        return ir

    @property
    def asm(self):
        asm = build_asm_output(self)
        self.__dict__["asm"] = asm
        return asm

    @property
    def opcodes(self):
        return build_opcodes_output(self)

    @property
    def runtime_opcodes(self):
        return build_opcodes_output(self)

    @property
    def external_interface(self):
        return build_external_interface_output(self)

    @property
    def layout(self):
        return build_layout_output(self)


def generate_compiler_data(src: str, name="DasyContract", filepath: str = None) -> CompilerData:
    (ast, settings) = parse_src(src, filepath)
    settings = Settings(**settings)
    
    # Create a FileInput object
    from vyper.compiler.input_bundle import FileInput
    file_input = FileInput(
        contents=src,
        source_id=0,
        path=filepath or f"{name}.dasy",
        resolved_path=filepath or f"{name}.dasy"
    )
    
    with anchor_settings(settings):
        data = CompilerData(
            file_input,
            settings=settings,
        )
        # Override the vyper_module with our parsed AST
        data.__dict__["vyper_module"] = ast
        _ = data.bytecode
        return data


def compile(src: str, name="DasyContract", include_abi=True, filepath: str = None) -> CompilerData:
    data = generate_compiler_data(src, name, filepath)
    return data


def compile_file(filepath: str) -> CompilerData:
    path = Path(filepath)
    name = path.stem
    # name = ''.join(x.capitalize() for x in name.split('_'))
    with path.open() as f:
        src = f.read()
        if filepath.endswith(".vy"):
            return CompilerData(src, contract_name=filename_to_contract_name(filepath))
        return compile(src, name=name, filepath=filepath)


def generate_abi(src: str) -> list:
    return compile(src).abi
