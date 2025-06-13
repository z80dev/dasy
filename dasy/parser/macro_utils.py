"""Utilities for macro compilation that avoid circular dependencies."""

from pathlib import Path
from typing import Optional, Set
import threading
from vyper.compiler import CompilerData
from vyper.compiler.settings import Settings, anchor_settings

from dasy.exceptions import DasyCircularDependencyError

# Thread-local storage for tracking compilation stack
_thread_local = threading.local()


def get_compilation_stack() -> Set[str]:
    """Get the current compilation stack for this thread."""
    if not hasattr(_thread_local, 'compilation_stack'):
        _thread_local.compilation_stack = set()
    return _thread_local.compilation_stack


def compile_for_interface(filepath: str) -> CompilerData:
    """
    Compile a file just enough to extract its interface.
    This avoids full compilation and helps prevent circular dependencies.
    """
    path = Path(filepath)
    abs_path = str(path.absolute())
    
    # Check for circular dependencies
    stack = get_compilation_stack()
    if abs_path in stack:
        raise DasyCircularDependencyError(
            f"Circular dependency detected: {abs_path} is already being compiled. "
            f"Compilation stack: {list(stack)}",
            path=abs_path,
            stack=list(stack)
        )
    
    # Add to compilation stack
    stack.add(abs_path)
    
    try:
        with path.open() as f:
            src = f.read()
        
        # For .vy files, use Vyper's compiler directly
        if filepath.endswith(".vy"):
            from vyper.compiler import CompilerData as VyperCompilerData
            from dasy.parser.utils import filename_to_contract_name
            return VyperCompilerData(src, contract_name=filename_to_contract_name(filepath))
        
        # For .dasy files, we need minimal compilation
        # Import here to avoid circular imports
        from dasy.parser import parse_src
        
        # Parse with minimal processing - just enough to get the interface
        ast, settings = parse_src(src, filepath)
        settings = Settings(**settings)
        with anchor_settings(settings):
            # Create minimal compiler data
            from dasy.compiler import CompilerData as DasyCompilerData
            data = DasyCompilerData(
                "",
                path.stem,
                None,
                source_id=0,
                settings=settings,
            )
            data.vyper_module = ast
            
            # Only process enough to get the external interface
            # This avoids full bytecode generation
            _ = data.vyper_module_folded  # This is enough for interface extraction
            
            return data
    finally:
        # Always remove from compilation stack
        stack.discard(abs_path)


def clear_compilation_stack():
    """Clear the compilation stack (useful for testing)."""
    if hasattr(_thread_local, 'compilation_stack'):
        _thread_local.compilation_stack.clear()


def get_include_stack() -> Set[str]:
    """Get the current include stack for this thread."""
    if not hasattr(_thread_local, 'include_stack'):
        _thread_local.include_stack = set()
    return _thread_local.include_stack


def check_include_recursion(filepath: str) -> None:
    """Check if including this file would create a circular dependency."""
    abs_path = str(Path(filepath).absolute())
    stack = get_include_stack()
    
    if abs_path in stack:
        raise DasyCircularDependencyError(
            f"Circular include detected: {abs_path} is already being included. "
            f"Include stack: {list(stack)}",
            path=abs_path,
            stack=list(stack)
        )