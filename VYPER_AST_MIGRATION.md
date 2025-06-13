# Vyper AST Migration Guide for Dasy

## Summary

In Vyper 0.4.2, the `phases.generate_ast()` function has been replaced with `vyper.ast.parse_to_ast()`. This document explains how Vyper AST is generated in the current version and what changes were needed for Dasy.

## Key Changes

### 1. AST Parsing Function

**Old way (pre-0.4.2):**
```python
from vyper.compiler import phases
ast = phases.generate_ast(source_code, source_id, module_path)[1]
```

**New way (0.4.2+):**
```python
import vyper.ast
ast = vyper.ast.parse_to_ast(
    source_code,
    source_id=0,
    module_path="contract.vy",
    resolved_path="contract.vy"
)
```

### 2. Function Signature

The new `parse_to_ast` function has the following signature:
```python
def parse_to_ast(
    vyper_source: str,
    source_id: int = 0,
    module_path: Optional[str] = None,
    resolved_path: Optional[str] = None,
    add_fn_node: Optional[str] = None,
    is_interface: bool = False
) -> vyper.ast.nodes.Module
```

### 3. Module Attributes

The returned AST Module node requires these attributes to be set for proper compilation:
- `path`: The file path (string)
- `resolved_path`: The resolved file path (string)
- `source_id`: Integer ID for the source
- `full_source_code`: The original source code
- `is_interface`: Boolean indicating if it's an interface
- `settings`: A `vyper.compiler.settings.Settings` object

### 4. CompilerData Integration

When using CompilerData with custom ASTs:
- FileInput now expects `Path` objects instead of strings
- You can override `vyper_module` in CompilerData after creation
- The AST must have all required attributes set

## Changes Made to Dasy

### Fixed Import in `dasy/builtin/functions.py`

Changed the `parse_vyper` function from:
```python
def parse_vyper(expr):
    return phases.generate_ast(str(expr[1]), 0, "")[1].body[0]
```

To:
```python
def parse_vyper(expr):
    # Use vyper.ast.parse_to_ast instead of phases.generate_ast
    ast = vyper.ast.parse_to_ast(str(expr[1]), source_id=0)
    return ast.body[0]
```

## Usage Examples

### Parsing Vyper Code to AST
```python
import vyper.ast

# Parse Vyper source code
vyper_code = '''
@external
def greet(name: String[100]) -> String[100]:
    return concat("Hello, ", name)
'''

ast = vyper.ast.parse_to_ast(
    vyper_code,
    source_id=0,
    module_path='example.vy',
    resolved_path='example.vy'
)
```

### Creating CompilerData with Custom AST
```python
from vyper.compiler.phases import CompilerData
from vyper.compiler.input_bundle import FileInput
from vyper.compiler.settings import Settings
from pathlib import Path

# Create FileInput
file_input = FileInput(
    contents=source_code,
    source_id=0,
    path=Path("contract.vy"),
    resolved_path=Path("contract.vy")
)

# Create CompilerData
compiler_data = CompilerData(file_input, settings=Settings())

# Override with custom AST if needed
compiler_data.__dict__["vyper_module"] = custom_ast
```

## Notes

- The removal of `phases.generate_ast` is part of Vyper's ongoing refactoring to improve the compiler architecture
- The new `parse_to_ast` function is more explicit about its parameters and return type
- All existing Dasy functionality continues to work with this change