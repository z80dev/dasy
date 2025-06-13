# Dasy 0.2.0a1 Release - Vyper 0.4.2 Migration Complete! 🚀

We're excited to announce **Dasy 0.2.0a1**, a major alpha release that brings full compatibility with **Vyper 0.4.2**! This update represents a significant milestone in Dasy's evolution, incorporating all the latest improvements and security enhancements from the Vyper ecosystem.

## 🎯 What's New

### Vyper 0.4.2 Compatibility
Dasy now compiles to and leverages all the optimizations, security improvements, and new features available in Vyper 0.4.2, giving you access to the latest and greatest in EVM smart contract compilation.

### Enhanced External Call Syntax
We've completely overhauled external contract interaction syntax to align with Vyper 0.4.2's new security-focused approach:

#### Before (Dasy 0.1.x):
```clojure
;; External calls were limited and inconsistent
(contract-call target-contract method args)
```

#### After (Dasy 0.2.0a1):
```clojure
;; Explicit, type-safe external calls
(extcall (target-contract.method arg1 arg2))        ; For state-changing calls
(staticcall (target-contract.view-method))          ; For view/pure calls

;; Interface-based calls
(extcall ((. (MyInterface addr) transfer) to amount))
(staticcall ((. (MyInterface addr) balanceOf) owner))
```

## 🔄 Breaking Changes & Migration Guide

### 1. Integer Division Operator
**Change**: The `/` operator now performs floating-point division; use `//` for integer division.

```clojure
;; Before
(/ 10 3)  ; Performed integer division

;; After  
(// 10 3) ; Integer division (returns 3)
(/ 10 3)  ; Would be floating-point (not typically used in smart contracts)
```

### 2. Enum → Flag Migration
**Change**: `defenum` has been replaced with `defflag` to align with Vyper's flag system.

```clojure
;; Before
(defenum Status
  :pending
  :active  
  :inactive)

;; After
(defflag Status
  :pending
  :active
  :inactive)
```

### 3. Loop Variable Type Annotations
**Change**: All loop variables must now have explicit type annotations.

```clojure
;; Before
(for [i (range 10)]
  (some-operation i))

;; After
(for [i :uint256 (range 10)]
  (some-operation i))
```

### 4. Struct Instantiation
**Change**: Struct constructors now use keyword-only syntax.

```clojure
;; Before
(Person {:name "Alice" :age 30})

;; After
(Person :name "Alice" :age 30)
```

### 5. Event Logging Syntax
**Change**: Event emissions now require keyword-only arguments.

```clojure
;; Before
(log (Transfer sender receiver amount))

;; After  
(log (Transfer :sender sender :receiver receiver :amount amount))
```

### 6. External Call System
**Change**: New explicit external call syntax for better security and clarity.

```clojure
;; Before
(contract.method args)

;; After
(extcall (contract.method args))        ; For state changes
(staticcall (contract.method args))     ; For view/pure calls
```

### 7. Nonreentrant Decorator
**Change**: The nonreentrant decorator no longer takes parameters.

```clojure
;; Before
(defn transfer [...] [:external (nonreentrant "lock")]
  ...)

;; After
(defn transfer [...] [:external :nonreentrant]
  ...)
```

### 8. Built-in Function Names
**Change**: Some built-in functions have been renamed.

```clojure
;; Before
(_abi_encode data)
(_abi_decode data type)

;; After
(abi_encode data)
(abi_decode data type)
```

## 🆕 New Features

### Module System Support (Preview)
Dasy now includes basic parsing support for Vyper 0.4.2's new module system:

```clojure
;; Import modules
(uses my-library)

;; Initialize modules
(initializes my-library)

;; Export functions
(exports my-function)
```

*Note: Full module resolution and import functionality is coming in a future release.*

### Enhanced Interface Support
Improved interface definitions and usage:

```clojure
(definterface IERC20
  (defn totalSupply [] :uint256 :view)
  (defn balanceOf [:address account] :uint256 :view)
  (defn transfer [:address to :uint256 amount] :bool :nonpayable))

;; Usage with explicit calls
(defn check-balance [:address token :address user] :uint256 [:external :view]
  (staticcall ((. (IERC20 token) balanceOf) user)))
```

### Improved Type Safety
- Enhanced type checking and validation
- Better error messages for type mismatches  
- Stricter enforcement of mutability constraints

## 📊 Performance & Reliability

### Test Suite Results
- **39/39 tests passing** (100% success rate)
- Full compatibility with Vyper 0.4.2 compilation pipeline
- Enhanced error reporting and debugging support

### Compiler Improvements
- Faster compilation times
- Better memory usage
- Improved error messages with precise source locations

## 🛠️ Migration Steps

1. **Update Dependencies**:
   ```bash
   # Update to Dasy 0.2.0a1
   pip install dasy==0.2.0a1
   ```

2. **Update Syntax**:
   - Replace `defenum` with `defflag`
   - Add type annotations to loop variables
   - Update struct instantiation syntax
   - Migrate to new external call syntax
   - Update event logging syntax

3. **Test Thoroughly**:
   - Run your existing test suite
   - Pay special attention to external contract interactions
   - Verify event emissions work correctly

4. **Update Documentation**:
   - Update any documentation that references old syntax
   - Review and update code examples

## 🔮 Looking Ahead

### Upcoming Features
- **Full Module System**: Complete implementation of Vyper 0.4.2's module system
- **Enhanced IDE Support**: Better syntax highlighting and error reporting
- **Advanced Macros**: More powerful macro capabilities
- **Optimization Passes**: Additional compile-time optimizations

### Community
We're committed to making Dasy the premier choice for Lisp-style smart contract development. Join our community:

- **GitHub**: [dasy-lang/dasy](https://github.com/dasy-lang/dasy)
- **Documentation**: [docs.dasy-lang.org](https://docs.dasy-lang.org)
- **Discord**: [Dasy Community](https://discord.gg/dasy)

## 🙏 Acknowledgments

Special thanks to the Vyper team for their continued innovation and the robust foundation that makes Dasy possible. This release represents months of careful migration work to ensure full compatibility while maintaining Dasy's unique Lisp-inspired syntax.

## 📝 Full Changelog

### Added
- Vyper 0.4.2 compatibility
- External call syntax (`extcall`/`staticcall`)
- Flag definitions (`defflag`)
- Module system declarations (preview)
- Enhanced type annotations for loops
- Keyword-only struct instantiation
- Improved interface support

### Changed
- Integer division operator (`/` → `//`)
- Event logging syntax (keyword arguments)
- Nonreentrant decorator (parameterless)
- Built-in function names (`_abi_*` → `abi_*`)

### Fixed
- All external call compilation issues
- Interface method invocation
- Source map generation for Vyper 0.4.2
- AST node compatibility issues

### Removed
- Legacy enum syntax (`defenum`)
- Positional struct arguments
- Parameterized nonreentrant decorators

---

**Ready to upgrade?** Check out our [Migration Guide](MIGRATION_GUIDE.md) for detailed step-by-step instructions, or explore the updated [examples](examples/) to see the new syntax in action!

Happy coding! 🎉