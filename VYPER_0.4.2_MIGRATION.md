# Vyper 0.4.2 Migration Progress

## Overview
This document tracks the progress of migrating Dasy from Vyper 0.3.10 to Vyper 0.4.2.

## Completed Changes

### 1. Dependencies Updated ✅
- Updated `pyproject.toml` to use `vyper==0.4.2`
- Updated imports to use new module locations

### 2. AST Node Updates ✅
- **Removed Index node**: Subscripts now directly use slice value without wrapping in Index
- **Updated imports**: Replaced `anchor_evm_version` with `anchor_settings` from compiler.settings
- **Fixed _children**: Changed from set to list (`.add()` → `.append()`)

### 3. External Call Syntax ✅
- Added support for new explicit external call syntax:
  - `(extcall contract.method args...)` for external calls
  - `(staticcall contract.method args...)` for static calls
- Added `ExtCall` and `StaticCall` AST node imports and parsing functions

### 4. Enum to Flag ✅
- Changed `defenum` keyword to `defflag`
- Updated parser to use `FlagDef` instead of `EnumDef`
- Renamed `examples/enum.dasy` to `examples/flag.dasy`

## Current Issues

### Module Node Structure
The Module AST node in Vyper 0.4.2 requires additional attributes:
- `path`: File path
- `resolved_path`: Resolved file path  
- `source_id`: Source ID for the file
- `full_source_code`: Complete source code
- `is_interface`: Boolean flag
- `settings`: Settings object

### CompilerData Initialization
- Now requires `FileInput` object instead of direct arguments
- Changed constructor signature significantly

### Missing Module Integration
- FunctionDef nodes need `module_node` attribute
- Need to properly set parent-child relationships in AST

## Remaining Syntax Changes

### 1. Integer Division
- Need to update `/` operator to `//` for integer division
- Regular `/` is no longer allowed for integers

### 2. Struct Instantiation
- Must use keyword arguments: `(MyStruct :field1 val1 :field2 val2)`
- Positional arguments no longer allowed

### 3. Loop Variables
- Require type annotations: `(for [i :uint256] (range 10) ...)`

### 4. Built-in Function Updates
- `_abi_encode` → `abi_encode`
- `_abi_decode` → `abi_decode`
- Removed builtin constants
- `sqrt()` moved to stdlib math module

### 5. Other Breaking Changes
- `@internal` decorator now optional
- Removed named reentrancy locks
- Default nonreentrancy for all functions
- Cannot call `__default__` directly
- Ban calling nonreentrant from nonreentrant

## Next Steps

1. Fix Module node initialization and AST structure
2. Update remaining syntax changes
3. Fix test suite for Vyper 0.4.2
4. Update all examples
5. Document migration guide for users

## Module System Integration

The new module system in Vyper 0.4.0+ includes:
- `uses` declarations for module imports
- `initializes` for module initialization
- `exports` for function/interface exports
- Stateless modules with ownership hierarchy

This will require significant updates to how Dasy handles module-level code organization.