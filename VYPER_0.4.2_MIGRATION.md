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

## Current Issues - RESOLVED ✅

### Module Node Structure ✅
The Module AST node in Vyper 0.4.2 requires additional attributes:
- `path`: File path - **FIXED**
- `resolved_path`: Resolved file path - **FIXED**
- `source_id`: Source ID for the file - **FIXED**
- `full_source_code`: Complete source code - **FIXED**
- `is_interface`: Boolean flag - **FIXED**
- `settings`: Settings object - **FIXED**

### CompilerData Initialization ✅
- Now requires `FileInput` object instead of direct arguments - **FIXED**
- Changed constructor signature significantly - **FIXED**

### AST Parent-Child Relationships ✅
- Properly set parent-child relationships in AST - **FIXED**
- Fixed kebab-case to snake_case conversion for function names - **FIXED**

### Basic Compilation ✅
- Simple contracts now compile successfully!
- Fixed "Unsupported syntax for function namespace" error

## Completed Syntax Changes ✅

### 1. Integer Division ✅
- Updated `/` operator to `//` for integer division
- Added `//` operator support in parser
- Regular `/` is reserved for decimal division

### 2. Struct Instantiation ✅ 
- Must use keyword arguments: `(MyStruct :field1 val1 :field2 val2)`
- Updated examples to use keyword syntax
- Parser already supported this syntax

### 3. Loop Variables ✅
- Require type annotations: `(for [i :uint256 xs] ...)`
- Updated parser to handle typed loop variables
- Old syntax without types no longer supported

## Remaining Syntax Changes

### 4. Built-in Function Updates ✅
- `_abi_encode` → `abi_encode` - **Added alias mapping**
- `_abi_decode` → `abi_decode` - **Added alias mapping**
- Removed builtin constants
- `sqrt()` moved to stdlib math module

### 5. Other Breaking Changes ✅
- `@internal` decorator now optional
- Removed named reentrancy locks
- Default nonreentrancy for all functions
- Cannot call `__default__` directly
- Ban calling nonreentrant from nonreentrant
- Constructor must use `@deploy` instead of `@external` - **FIXED**

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