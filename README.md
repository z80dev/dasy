# Dasy

**A Lisp for the EVM that compiles to Vyper**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Vyper 0.4.3](https://img.shields.io/badge/vyper-0.4.3-purple.svg)](https://github.com/vyperlang/vyper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> *The Dasypeltis, gansi, is considered an egg-eating snake. Their diet consists of all forms of eggs considering they have no teeth in which to eat living prey with.*

Dasy is an experimental smart contract programming language in the Lisp family. It combines the expressive power of Lisp with the safety and optimization of Vyper, giving you:

- **Lisp syntax** with Clojure-inspired conventions
- **Powerful macro system** for compile-time code transformation
- **Vyper's security guarantees** including bounds checking and overflow protection
- **Vyper's optimizations** producing efficient EVM bytecode
- **Seamless interop** with existing Vyper contracts and tools

---

## Table of Contents

- [Quick Start](#quick-start)
- [Why Dasy?](#why-dasy)
- [Installation](#installation)
- [Language Guide](#language-guide)
  - [Basic Syntax](#basic-syntax)
  - [Types](#types)
  - [Variables and Storage](#variables-and-storage)
  - [Functions](#functions)
  - [Control Flow](#control-flow)
  - [Data Structures](#data-structures)
  - [Events](#events)
  - [Interfaces and External Calls](#interfaces-and-external-calls)
  - [Error Handling](#error-handling)
- [Macro System](#macro-system)
  - [Built-in Macros](#built-in-macros)
  - [Defining Custom Macros](#defining-custom-macros)
- [Tools](#tools)
  - [dasy2vyper](#dasy2vyper)
  - [vyper2dasy](#vyper2dasy)
- [Complete Examples](#complete-examples)
- [CLI Reference](#cli-reference)
- [Framework Integration](#framework-integration)
- [Contributing](#contributing)

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/dasylang/dasy.git
cd dasy
uv sync --dev

# Compile your first contract
uv run dasy examples/hello_world.dasy
```

Here's a simple Dasy contract:

```clojure
;; hello_world.dasy
(defvar greet (public (string 100)))

(defn __init__ [] :external
  (set self/greet "Hello World"))
```

Compile it:

```bash
uv run dasy hello_world.dasy -f abi        # Get ABI
uv run dasy hello_world.dasy -f bytecode   # Get bytecode
uv run dasy hello_world.dasy -f ir         # See intermediate representation
```

---

## Why Dasy?

### The Power of Lisp for Smart Contracts

Smart contracts benefit enormously from Lisp's macro system. Macros allow you to:

- **Reduce boilerplate** - Define patterns once, use everywhere
- **Create domain-specific abstractions** - Tailor the language to your needs
- **Prototype language features** - Test ideas before implementing in the compiler

### Vyper as a Backend

By compiling to Vyper, Dasy inherits all of Vyper's safety features:

- **No integer overflow/underflow** - All arithmetic is checked
- **Bounded loops** - No unbounded iteration that could run out of gas
- **No recursive calls** - Prevents reentrancy by design
- **Static typing** - Catch errors at compile time
- **Readable output** - Generated Vyper is human-readable

### Syntax Comparison

Here's the same logic in nested `if` statements vs. the `cond` macro:

```clojure
;; Deeply nested if statements
(defn useIf [[x uint256]] uint256 :external
  (if (<= x 10)
      1
      (if (<= x 20)
          2
          3)))

;; Clean cond macro - same logic, much clearer
(defn useCond [[x uint256]] uint256 :external
  (cond
    (<= x 10) 1
    (<= x 20) 2
    :else     3))

;; condp - even cleaner when comparing against the same value
(defn useCondp [[x uint256]] uint256 :external
  (condp <= x
    10 1
    20 2
    :else 3))
```

---

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/dasylang/dasy.git
cd dasy

# Install with development dependencies
uv sync --dev

# Run dasy
uv run dasy examples/hello_world.dasy
```

### As a Library

```bash
uv pip install git+https://github.com/dasylang/dasy.git
```

### As an Executable via pipx

```bash
pipx install git+https://github.com/dasylang/dasy.git
```

### Framework Plugins

- **[Ape Plugin](https://github.com/dasylang/ape-dasy)**: `pip install ape-dasy`
- **[Foundry Plugin](https://github.com/dasylang/foundry-dasy)**: See repository for installation

---

## Language Guide

### Basic Syntax

Dasy uses S-expressions (symbolic expressions) - everything is either an atom or a list:

```clojure
;; Comments start with semicolons

;; Function calls: (function arg1 arg2 ...)
(+ 1 2)           ; => 3
(* 3 4)           ; => 12

;; Attribute access uses /
msg/sender        ; => msg.sender in Vyper
self/balance      ; => self.balance in Vyper
block/timestamp   ; => block.timestamp in Vyper

;; Or use the dot form explicitly
(. msg sender)    ; => msg.sender
(. self balance)  ; => self.balance
```

### Types

Dasy supports all Vyper types using symbol syntax:

```clojure
;; Integer types
uint256  uint128  uint64  uint32  uint16  uint8
int256   int128   int64   int32   int16   int8

;; Other primitives
address
bool
bytes32  bytes4  bytes20
decimal

;; Parameterized types
(string 100)              ; String with max 100 chars
(bytes 32)                ; Bytes with max 32 bytes
(dyn-array uint256 10)    ; Dynamic array, max 10 elements
(array uint256 5)         ; Fixed-size array of 5 elements
(hash-map address uint256) ; Mapping from address to uint256
```

### Variables and Storage

#### Storage Variables

```clojure
;; Single storage variable
(defvar owner (public address))

;; Multiple storage variables with defvars
(defvars
  :public                                    ; visibility modifier
  name (string 32)
  symbol (string 32)
  decimals uint8
  totalSupply uint256
  balanceOf (hash-map address uint256))

;; Private storage (omit :public)
(defvars
  _internalCounter uint256
  _adminList (dyn-array address 100))
```

#### Local Variables

```clojure
(defn example [] uint256 :external
  ;; Local variable with type annotation
  (defvar x uint256 10)

  ;; Local variable with initial value from expression
  (defvar y uint256 (* x 2))

  ;; Fixed array literal
  (defvar nums (array uint256 3) [1 2 3])

  y)
```

#### Constants and Immutables

```clojure
;; Compile-time constant
(defconst MAX_SUPPLY uint256 1000000)

;; Immutable (set once in constructor)
(defvar OWNER (immutable address))

(defn __init__ [] :external
  (set OWNER msg/sender))
```

### Functions

#### Function Syntax

```clojure
;; Basic syntax:
;; (defn name [[arg1 type1] [arg2 type2]] return-type decorators body...)

;; External function with return type
(defn add [[x uint256] [y uint256]] uint256 :external
  (+ x y))

;; Multiple decorators use a list
(defn pureAdd [[x uint256] [y uint256]] uint256 [:external :pure]
  (+ x y))

;; No return type (implicitly None)
(defn setOwner [[newOwner address]] :external
  (set self/owner newOwner))

;; Internal function (callable only from this contract)
(defn _internalHelper [[x uint256]] uint256 :internal
  (* x 2))

;; View function (reads state but doesn't modify)
(defn getBalance [] uint256 [:external :view]
  self/totalSupply)

;; Payable function (can receive Ether)
(defn deposit [] [:external :payable]
  (+= self/deposits msg/value))
```

#### Function Visibility

| Decorator | Description |
|-----------|-------------|
| `:external` | Callable from outside the contract |
| `:internal` | Only callable from within the contract |
| `:view` | Reads state but doesn't modify it |
| `:pure` | Doesn't read or modify state |
| `:payable` | Can receive Ether |
| `:nonreentrant` | Protected against reentrancy |

### Control Flow

#### If Expressions

```clojure
;; if returns a value
(defn absoluteValue [[x uint256] [y uint256]] uint256 [:external :pure]
  (if (>= x y)
      (- x y)
      (- y x)))

;; Assign result of if to variable
(defvar result uint256
  (if (> x 10) 100 0))
```

#### Cond (Multi-way Branch)

```clojure
(defn classify [[x uint256]] uint256 :external
  (cond
    (< x 10)  1
    (< x 100) 2
    (< x 1000) 3
    :else     4))
```

#### When and Unless

```clojure
;; when - execute body if condition is true
(when (== msg/sender self/owner)
  (set self/paused True)
  (log (Paused)))

;; unless - execute body if condition is false
(unless self/paused
  (self/_processTransaction amount))
```

#### For Loops

```clojure
;; Range-based loop (literal bound)
(defn sumTo10 [] uint256 [:external :pure]
  (defvar total uint256 0)
  (for [i uint256 (range 10)]
    (+= total i))
  total)

;; Range with variable requires :bound
(defn sumToN [[n uint256]] uint256 [:external :pure]
  (defvar total uint256 0)
  (for [i uint256 (range n :bound 256)]
    (+= total i))
  total)

;; Loop over array
(defn sumArray [[nums (array uint256 10)]] uint256 [:external :pure]
  (defvar total uint256 0)
  (for [n uint256 nums]
    (+= total n))
  total)

;; Loop with break and continue
(defn findFirst [[nums (array uint256 10)] [target uint256]] uint256 :external
  (defvar result uint256 0)
  (for [i uint256 (range 10)]
    (if (== (subscript nums i) target)
        (do
          (set result i)
          (break)))
    (if (== (subscript nums i) 0)
        (continue)))
  result)
```

### Data Structures

#### Arrays

```clojure
;; Fixed-size array
(defvar nums (public (array uint256 10)))

;; Dynamic array with max size
(defvar items (public (dyn-array uint256 100)))

;; Array operations
(defn arrayOps [] :external
  ;; Append to dynamic array
  (.append self/items 42)

  ;; Access by index
  (defvar first uint256 (subscript self/nums 0))

  ;; Or use get-at macro
  (defvar second uint256 (get-at self/nums 1))

  ;; Set by index
  (set-at self/nums 0 100))
```

#### Hash Maps

```clojure
(defvar balances (public (hash-map address uint256)))
(defvar allowances (public (hash-map address (hash-map address uint256))))

(defn mapOps [] :external
  ;; Get value
  (defvar bal uint256 (get-at self/balances msg/sender))

  ;; Set value
  (set-at self/balances msg/sender 100)

  ;; Nested map access
  (defvar allowed uint256 (get-at self/allowances msg/sender self/spender))
  (set-at self/allowances msg/sender self/spender 50))
```

#### Structs

```clojure
;; Define a struct
(defstruct Person
  name (string 100)
  age uint256)

(defvar person (public Person))

(defn structOps [] :external
  ;; Create struct literal
  (defvar p Person (Person :name "Alice" :age 30))

  ;; Access fields
  (defvar personAge uint256 (. self/person age))

  ;; Set fields using set-in
  (set-in self/person age 31)
  (set-in self/person name "Bob"))
```

#### Flags (Enums)

```clojure
(defflag Roles
  ADMIN
  USER
  MODERATOR)

(defvar userRoles (public (hash-map address Roles)))

(defn checkRole [] bool [:external :view]
  (== (get-at self/userRoles msg/sender) Roles/ADMIN))
```

### Events

```clojure
;; Define an event
(defevent Transfer
  sender (indexed address)
  receiver (indexed address)
  amount uint256)

(defevent Approval
  owner (indexed address)
  spender (indexed address)
  value uint256)

;; Emit events with log
(defn transfer [[to address] [amount uint256]] :external
  ;; ... transfer logic ...
  (log (Transfer :sender msg/sender :receiver to :amount amount)))
```

### Interfaces and External Calls

#### Defining Interfaces

```clojure
(definterface IERC20
  (defn totalSupply [] uint256 :view)
  (defn balanceOf [[owner address]] uint256 :view)
  (defn transfer [[to address] [amount uint256]] bool :nonpayable)
  (defn approve [[spender address] [amount uint256]] bool :nonpayable))
```

#### External Calls

```clojure
(defvar token (public IERC20))

(defn __init__ [[tokenAddr address]] :external
  (set self/token (IERC20 tokenAddr)))

;; staticcall for view/pure functions
(defn getTokenBalance [[owner address]] uint256 [:external :view]
  (staticcall (. self/token balanceOf owner)))

;; extcall for state-changing functions
(defn sendTokens [[to address] [amount uint256]] :external
  (extcall (. self/token transfer to amount)))
```

#### Raw Calls

```clojure
(defn rawCallExample [[to address] [x uint256] [y uint256]] uint256 :external
  (defvar result (bytes 32)
    (raw_call to
              (concat (method_id "multiply(uint256,uint256)")
                      (convert x bytes32)
                      (convert y bytes32))
              :max_outsize 32
              :gas 100000
              :value 0))
  (convert result uint256))
```

### Error Handling

```clojure
;; Assert with message
(defn withdraw [[amount uint256]] :external
  (assert (>= (get-at self/balances msg/sender) amount) "Insufficient balance")
  (assert (!= amount 0) "Amount must be non-zero")
  ;; ... withdrawal logic ...
  )

;; Raise (revert) with message
(defn onlyOwner [] :internal
  (if (!= msg/sender self/owner)
      (raise "Not authorized")))
```

---

## Macro System

Dasy's macro system allows you to transform code at compile time, enabling powerful abstractions without runtime overhead.

### Built-in Macros

| Macro | Description | Example |
|-------|-------------|---------|
| `cond` | Multi-way conditional | `(cond test1 expr1 test2 expr2 :else default)` |
| `condp` | Conditional with shared predicate | `(condp <= x 10 "small" 100 "medium" :else "large")` |
| `when` | Execute body if true | `(when condition body...)` |
| `unless` | Execute body if false | `(unless condition body...)` |
| `let` | Local bindings | `(let [x 1 y 2] (+ x y))` |
| `->` | Thread-first | `(-> x (f a) (g b))` => `(g (f x a) b)` |
| `->>` | Thread-last | `(->> x (f a) (g b))` => `(g b (f a x))` |
| `doto` | Apply multiple operations | `(doto obj (f a) (g b))` |
| `get-at` | Nested subscript access | `(get-at map key1 key2)` |
| `set-at` | Nested subscript assignment | `(set-at map key1 key2 value)` |
| `set-in` | Struct field assignment | `(set-in struct field value)` |
| `set-self` | Batch set self fields | `(set-self name symbol decimals)` |
| `inc` | Increment by 1 | `(inc counter)` => `(+= counter 1)` |
| `dec` | Decrement by 1 | `(dec counter)` => `(-= counter 1)` |
| `hash-map` | HashMap type constructor | `(hash-map address uint256)` |
| `dyn-array` | DynArray type constructor | `(dyn-array uint256 10)` |
| `string` | String type constructor | `(string 100)` |
| `bytes` | Bytes type constructor | `(bytes 32)` |
| `include!` | Include another Dasy file | `(include! "lib/utils.dasy")` |
| `interface!` | Import interface from file | `(interface! "interfaces/IERC20.vy")` |

### Threading Macros

Threading macros make deeply nested function calls readable:

```clojure
;; Without threading - read inside out
(send self/beneficiary (get-at self/pendingReturns self/highestBidder))

;; With thread-last (->>), read top to bottom
(->> self/highestBidder
     (get-at self/pendingReturns)
     (send self/beneficiary))

;; Thread-first example
(-> auction_start
    (+ bidding_time)
    (set self/auctionEnd))
```

### The doto Macro

Apply multiple operations to the same object:

```clojure
;; Without doto
(.append self/nums 11)
(.append self/nums 22)
(.append self/nums 33)

;; With doto
(doto self/nums
  (.append 11)
  (.append 22)
  (.append 33))

;; Works with set-at too
(doto self/balances
  (set-at addr1 100)
  (set-at addr2 200)
  (set-at addr3 300))
```

### Defining Custom Macros

Use `define-syntax` with `syntax-rules` to create pattern-based macros:

```clojure
;; Define an infix macro
(define-syntax infix
  (syntax-rules ()
    ((infix (a op b)) (op a b))))

;; Now you can write
(infix (x + y))  ; expands to (+ x y)

;; More complex example: swap macro
(define-syntax swap
  (syntax-rules ()
    ((swap a b)
     (do
       (defvar _temp uint256 a)
       (set a b)
       (set b _temp)))))
```

### Debugging Macros

Use the `expand` output format to see how macros expand:

```bash
uv run dasy mycontract.dasy -f expand
```

---

## Tools

### dasy2vyper

Convert Dasy source code to Vyper source code:

```bash
# Convert and print to stdout
uv run dasy2vyper examples/ERC20.dasy

# Save to file
uv run dasy2vyper examples/ERC20.dasy > ERC20.vy
```

This is useful for:
- Reviewing generated Vyper code
- Integrating with Vyper-only tooling
- Learning how Dasy constructs map to Vyper

**Example output:**

```python
# Input: examples/event.dasy
event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    amount: uint256

@external
def transfer(receiver: address, amount: uint256):
    log Transfer(sender=msg.sender, receiver=receiver, amount=amount)
```

### vyper2dasy

Convert existing Vyper contracts to Dasy (best-effort):

```bash
# Convert Vyper to Dasy
uv run vyper2dasy MyContract.vy

# Convert and verify the result compiles
uv run vyper2dasy MyContract.vy --check
```

This is useful for:
- Migrating existing Vyper codebases to Dasy
- Learning Dasy syntax from familiar Vyper code
- Enabling macro usage in existing contracts

---

## Complete Examples

### ERC20 Token

```clojure
(defevent Transfer
  sender (indexed address)
  receiver (indexed address)
  value uint256)

(defevent Approval
  owner (indexed address)
  spender (indexed address)
  value uint256)

(defvars
  :public
  name (string 32)
  symbol (string 32)
  decimals uint8
  balanceOf (hash-map address uint256)
  allowance (hash-map address (hash-map address uint256))
  totalSupply uint256
  minter address)

(defn __init__ [[name (string 32)] [symbol (string 32)] [decimals uint8] [supply uint256]] :external
  (defvar totalSupply uint256 (* supply (** 10 (convert decimals uint256))))
  (set-self name symbol decimals totalSupply)
  (set-at self/balanceOf msg/sender totalSupply)
  (set self/minter msg/sender)
  (log (Transfer :sender (empty address) :receiver msg/sender :value totalSupply)))

(defn transfer [[to address] [val uint256]] bool :external
  (doto (get-at self/balanceOf msg/sender) (-= val))
  (doto (get-at self/balanceOf to) (+= val))
  (log (Transfer :sender msg/sender :receiver to :value val))
  True)

(defn transferFrom [[_from address] [_to address] [val uint256]] bool :external
  (doto (get-at self/balanceOf _from) (-= val))
  (doto (get-at self/balanceOf _to) (+= val))
  (doto (get-at self/allowance _from msg/sender) (-= val))
  (log (Transfer :sender _from :receiver _to :value val))
  True)

(defn approve [[spender address] [val uint256]] bool :external
  (set-at self/allowance msg/sender spender val)
  (log (Approval :owner msg/sender :spender spender :value val))
  True)

(defn mint [[to address] [val uint256]] :external
  (assert (== msg/sender self/minter))
  (assert (!= to (empty address)))
  (+= self/totalSupply val)
  (doto (get-at self/balanceOf to) (+= val))
  (log (Transfer :sender (empty address) :receiver to :value val)))
```

### Simple Auction

```clojure
(defvars
  beneficiary (public address)
  auctionStart (public uint256)
  auctionEnd (public uint256)
  highestBidder (public address)
  highestBid (public uint256)
  ended (public bool)
  pendingReturns (public (hash-map address uint256)))

(defn __init__ [[beneficiary address] [auction_start uint256] [bidding_time uint256]] :external
  (set self/beneficiary beneficiary)
  (set self/auctionStart auction_start)
  (->> bidding_time
       (+ self/auctionStart)
       (set self/auctionEnd)))

(defn bid [] [:external :payable]
  (assert (>= block/timestamp self/auctionStart))
  (assert (< block/timestamp self/auctionEnd))
  (assert (> msg/value self/highestBid))
  (+= (subscript self/pendingReturns self/highestBidder) self/highestBid)
  (set self/highestBidder msg/sender)
  (set self/highestBid msg/value))

(defn withdraw [] :external
  (defvar pending_amount uint256 (get-at self/pendingReturns msg/sender))
  (set-at self/pendingReturns msg/sender 0)
  (send msg/sender pending_amount))

(defn endAuction [] :external
  (assert (>= block/timestamp self/auctionEnd))
  (assert (not self/ended))
  (set self/ended True)
  (send self/beneficiary self/highestBid))
```

---

## CLI Reference

```
dasy [-h] [-f FORMAT] [--evm-version VERSION] [--verbose] [--quiet] [--version] [filename]

Arguments:
  filename              Dasy source file to compile

Options:
  -h, --help            Show help message
  -f, --format FORMAT   Output format (see below)
  --evm-version VERSION Override EVM version (e.g., cancun, paris)
  --verbose             Enable debug logging
  --quiet               Suppress logs (errors only)
  --version             Show version number

Output Formats:
  bytecode (default)    Deployable bytecode
  bytecode_runtime      Runtime bytecode
  abi                   ABI in JSON format
  vyper_interface       Vyper interface definition
  external_interface    Dasy interface definition
  ir                    Intermediate representation
  ast                   AST in JSON format
  expand                Macro-expanded forms (for debugging)
  opcodes               EVM opcodes as string
  layout                Storage layout
  source_map            Source map for debugging
```

---

## Framework Integration

### Ape Framework

```bash
pip install ape-dasy
```

Then place `.dasy` files in your `contracts/` directory and use them like any other contract.

### Foundry

See the [foundry-dasy](https://github.com/dasylang/foundry-dasy) repository for integration instructions.

### Testing with titanoboa

```python
import dasy
from boa.contracts.vyper.vyper_contract import VyperContract

# Compile from source
src = '''
(defvar value (public uint256))
(defn setValue [[v uint256]] :external
  (set self/value v))
'''
contract_data = dasy.compile(src, include_abi=True)
contract = VyperContract(contract_data)

# Or compile from file
contract_data = dasy.compile_file("examples/hello_world.dasy")
contract = VyperContract(contract_data)

# Interact with the contract
contract.setValue(42)
assert contract.value() == 42
```

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Setup

```bash
git clone https://github.com/dasylang/dasy.git
cd dasy
uv sync --dev
```

### Running Tests

```bash
uv run pytest                          # Run all tests
uv run pytest tests/test_dasy.py       # Run specific test file
uv run pytest -k "test_erc20"          # Run tests matching pattern
```

### Code Formatting

```bash
uv run black dasy/ tests/
```

---

## Resources

- [Dasy by Example](https://dasy-by-example.github.io) - Learn Dasy through examples
- [Vyper Documentation](https://docs.vyperlang.org) - Vyper language reference
- [GitHub Issues](https://github.com/dasylang/dasy/issues) - Report bugs or request features

---

## License

MIT License - see [LICENSE](LICENSE) for details.
