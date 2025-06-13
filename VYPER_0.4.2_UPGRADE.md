# Vyper 0.4.2 Upgrade Documentation

This document details the upgrade of Dasy from Vyper 0.3.10 to Vyper 0.4.2, completed on January 13, 2025.

## Overview

Dasy is a Lisp-family smart contract language that compiles to Vyper. This upgrade ensures compatibility with Vyper 0.4.2, which introduced significant breaking changes to the AST structure, syntax requirements, and module system.

## Breaking Changes Addressed

### 1. AST Node Structure Changes

#### Index Node Removal
- **Change**: Vyper 0.4.0+ removed the `Index` AST node
- **Impact**: Subscript operations previously wrapped slice values in `Index` nodes
- **Fix**: Updated `parse_subscript` to use slice values directly
```python
# Before: Subscript(slice=Index(value=slice_node), value=value_node)
# After:  Subscript(slice=slice_node, value=value_node)
```

#### Module Node Requirements
- **Change**: Module nodes require additional attributes in 0.4.2
- **Fix**: Added required attributes during Module construction:
  - `path`, `resolved_path`, `source_id`, `full_source_code`
  - `is_interface`, `settings`

#### Parent-Child Relationships
- **Change**: `_children` changed from set to list
- **Fix**: Updated all `.add()` calls to `.append()`

### 2. Syntax Changes

#### External Call Syntax
- **Change**: External calls require explicit `extcall` or `staticcall` keywords
- **Syntax**: 
  ```clojure
  ;; Before: (contract.method args...)
  ;; After:  (extcall contract.method args...)
  ;;         (staticcall contract.method args...)
  ```
- **Implementation**: Added `parse_extcall` and `parse_staticcall` functions

#### Enum to Flag
- **Change**: `enum` keyword replaced with `flag`
- **Syntax**:
  ```clojure
  ;; Before: (defenum Status PENDING APPROVED REJECTED)
  ;; After:  (defflag Status PENDING APPROVED REJECTED)
  ```
- **Fix**: Renamed `parse_defenum` to `parse_defflag`, updated `EnumDef` to `FlagDef`

#### Integer Division
- **Change**: `/` operator no longer allowed for integer division
- **Syntax**:
  ```clojure
  ;; Before: (/ a b)
  ;; After:  (// a b)  ; Integer division
  ;;         (/ a b)   ; Reserved for decimal division
  ```
- **Fix**: Added `//` operator support with `FloorDiv` node

#### Struct Instantiation
- **Change**: Structs require keyword arguments, positional args forbidden
- **Syntax**:
  ```clojure
  ;; Before: (Person {:name "Alice" :age 30})
  ;; After:  (Person :name "Alice" :age 30)
  ```
- **Note**: Parser already supported keyword syntax; updated examples

#### Loop Variable Type Annotations
- **Change**: Loop variables require explicit type annotations
- **Syntax**:
  ```clojure
  ;; Before: (for [i (range 10)] ...)
  ;; After:  (for [i :uint256 (range 10)] ...)
  ```
- **Fix**: Updated `parse_for` to handle typed loop variables

### 3. Decorator and Function Changes

#### Constructor Decorator
- **Change**: Constructors use `@deploy` instead of `@external`
- **Fix**: Updated `parse_defn` to use "deploy" for `__init__` functions

#### Built-in Function Renames
- **Changes**:
  - `_abi_encode` → `abi_encode`
  - `_abi_decode` → `abi_decode`
- **Fix**: Added alias mappings in `ALIASES` dictionary

### 4. Module System (Partial Support)

#### New Declarations
- **Added parsing for**:
  - `(uses module-name)` - Import modules
  - `(initializes module-name)` - Initialize modules
  - `(exports function-name)` - Export functions
- **Status**: Basic parsing implemented; full module resolution pending

## Implementation Details

### Key Files Modified

1. **pyproject.toml**
   - Updated Vyper dependency from 0.3.10 to 0.4.2

2. **dasy/parser/nodes.py**
   - Added imports: `ExtCall`, `StaticCall`, `UsesDecl`, `InitializesDecl`, `ExportsDecl`
   - Implemented parsing functions for new syntax
   - Updated `parse_for` for typed loop variables

3. **dasy/parser/core.py**
   - Changed constructor decorator from "external" to "deploy"
   - Added `kebab_to_snake` conversion for function names
   - Updated imports to use `anchor_settings`

4. **dasy/parser/parse.py**
   - Fixed Module node initialization with required attributes
   - Added module declaration support
   - Updated built-in function aliases

5. **dasy/parser/ops.py** & **dasy/parser/builtins.hy**
   - Added `//` operator for integer division

6. **dasy/compiler.py**
   - Added `source_map` property for titanoboa compatibility
   - Enhanced logging for debugging
   - Updated `CompilerData` initialization

7. **Examples Updated**
   - `examples/flag.dasy` (renamed from enum.dasy)
   - `examples/for_loop.dasy` - Added type annotations
   - `examples/reference_types.dasy` - Updated struct syntax

### Backward Compatibility Notes

- Old loop syntax without type annotations is **not supported** in Vyper 0.4.2
- Struct instantiation with dictionary syntax is **not supported**
- External calls without `extcall`/`staticcall` will need updating
- The `/` operator for integer division must be replaced with `//`

## Testing Status

- ✅ Basic compilation works
- ✅ Hello world example passes
- ✅ Many core tests pass
- ❌ Some tests need syntax updates (struct instantiation, loops)
- ❌ Full test suite needs comprehensive updates

## Future Work

1. **Complete Module System Implementation**
   - Module resolution and loading
   - Dependency tracking
   - Export/import validation

2. **Update Test Suite**
   - Fix tests using old struct instantiation syntax
   - Update loop tests with type annotations
   - Add tests for new features

3. **Documentation**
   - User migration guide
   - Updated syntax documentation
   - Module system usage guide

4. **Examples**
   - Create module system examples
   - Update remaining examples
   - Add Vyper 0.4.2 feature showcases

## Migration Checklist for Dasy Users

When upgrading Dasy code to work with this version:

- [ ] Replace `defenum` with `defflag`
- [ ] Add type annotations to all loop variables: `[var :type iter]`
- [ ] Update struct instantiation to use keywords: `(Struct :field value)`
- [ ] Replace `/` with `//` for integer division
- [ ] Use `extcall` for external contract calls
- [ ] Update any references to `_abi_encode`/`_abi_decode`
- [ ] Ensure constructors don't have explicit decorators (auto-decorated with `@deploy`)

## Conclusion

The Dasy compiler now successfully compiles contracts using Vyper 0.4.2. While some advanced features like the full module system require additional implementation, the core language features are fully functional with the new Vyper version.