import logging
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
from .vyper_compat import make_file_input, make_compiler_data

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


from vyper.compiler.phases import CompilerData as VyperCompilerData


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
    
    @property
    def source_map(self):
        """Source map for debugging - required by titanoboa"""
        if not hasattr(self, "_source_map"):
            # Generate source map using vyper's output module
            from vyper.compiler.output import build_source_map_output
            try:
                self._source_map = build_source_map_output(self)
                # Vyper 0.4.2 stores tuples (source_id, node_id) in pc_ast_map
                # Titanoboa expects pc_raw_ast_map with actual AST nodes
                if "pc_ast_map" in self._source_map:
                    # For compatibility with titanoboa, just provide an empty mapping
                    # This prevents crashes but won't give accurate source locations
                    self._source_map["pc_raw_ast_map"] = {}
            except Exception as e:
                logger.debug(f"Source map generation failed: {e}")
                # Provide minimal structure expected by titanoboa
                self._source_map = {
                    "pc_raw_ast_map": {},
                    "pc_ast_map": {},
                    "source_map": {}
                }
        return self._source_map


def generate_compiler_data(src: str, name="DasyContract", filepath: str = None) -> CompilerData:
    logger.debug(f"generate_compiler_data: name={name}, filepath={filepath}")
    (ast, settings) = parse_src(src, filepath)
    
    # Log AST structure
    logger.debug(f"Parsed AST type: {type(ast).__name__}")
    logger.debug(f"AST body length: {len(ast.body) if hasattr(ast, 'body') else 'no body'}")
    if hasattr(ast, 'body'):
        for i, node in enumerate(ast.body):
            logger.debug(f"  Body[{i}]: {type(node).__name__} - {getattr(node, 'name', 'N/A')}")
            if hasattr(node, 'body') and node.body:
                for j, child in enumerate(node.body):
                    logger.debug(f"    Child[{j}]: {type(child).__name__}")
                    if hasattr(child, 'value'):
                        logger.debug(f"      Value type: {type(child.value).__name__}")
    
    settings = Settings(**settings)
    logger.debug(f"Settings: {settings}")
    
    # Create a FileInput object (compat with Vyper 0.4.x)
    file_input = make_file_input(src, name, filepath)
    
    logger.debug(f"Created FileInput: path={file_input.path}")
    
    with anchor_settings(settings):
        try:
            data = make_compiler_data(file_input, settings)
            # Override the vyper_module with our parsed AST
            data.__dict__["vyper_module"] = ast
            logger.debug("CompilerData created, attempting to compile bytecode...")
            _ = data.bytecode
            logger.debug("Bytecode compilation successful")
            return data
        except Exception as e:
            logger.error(f"Compilation error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise


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
