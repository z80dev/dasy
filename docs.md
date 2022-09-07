- [Current Status](#org00bb22a)
- [Syntax](#org7678c69)
  - [Tuples](#org2ef4f33)
  - [Arrays](#org7120eb0)
  - [Types](#orgbcfa084)
- [Core Macros](#org2d1e0cd)
  - [`defn`](#orgb08ef90)
  - [`defvar`](#orga070630)
  - [`setv`](#org03a8bea)
  - [`definterface`](#orgcdd6191)
  - [`defstruct`](#orga0f8171)
  - [`defevent`](#orgcdac4ec)
  - [`/`](#org9cbb6cd)



<a id="org00bb22a"></a>

# Current Status

Dasy is currently in pre-alpha. The language&rsquo;s core is still being designed and implemented.


<a id="org7678c69"></a>

# Syntax

Dasy has a clojure-inspired lisp syntax with some influences from python. Some constructs are dasy-specific.


<a id="org2ef4f33"></a>

## Tuples

Tuples are represented by a quoted list such as `'(1 2 3)`

The vyper equivalent is `(1, 2, 3)`


<a id="org7120eb0"></a>

## Arrays

Arrays are represented by a bracketed list, such as `[1 2 3]`

The vyper equivalent is `[1, 2, 3]`


<a id="orgbcfa084"></a>

## Types

Dasy has all of Vyper&rsquo;s types. Base types such as `uint256` are represented with a dasy &rsquo;keyword&rsquo;, which uses a colon and an identifier. Complex types are represented with a function-call syntax. Arrays are created with `array`, or `dyn-array` for dynamic arrays.

| Vyper                    | Dasy                        |
|------------------------ |--------------------------- |
| `uint256`                | `:uint256`                  |
| `bool`                   | `:bool`                     |
| `bytes32`                | `:bytes32`                  |
| `String[10]`             | `(string 10)`               |
| `uint256[10]`            | `(array :uint256 10)`       |
| `HashMap[uint256, bool]` | `(hash-map :uint256 :bool)` |
| `DynArray[uint256, 5]`   | `(dyn-array :uint256 5)`    |


<a id="org2d1e0cd"></a>

# Core Macros


<a id="orgb08ef90"></a>

## `defn`

`(defn fn-name args [return-type] visibility & body)`

This special form declares and defines a function within a smart contract.

The `args` list may be an empty list, but must be present. Returning multiple values requires declaring the return type as a tuple.

The `return-type` object is optional. If present, it may be a single keyword representing the return type, or it may be a tuple of keywords for returning multiple values.

The `visibility` object may also be a keyword or list of keywords. Valid values are:

-   `:external`
-   `:internal`
-   `:payable`
-   `:view`
-   `:pure`
-   `(nonreentrant "lock-name")`

```clojure
(defn noArgs [] :external (pass))

(defn setNum [:uint256 x] :external (pass))

(defn addNums [:uint256 x y] :uint256 [:external :pure]
  (+ x y))

(defn addAndSub [:uint256 x y] '(:uint256 :uint256) [:external :pure]
  '((+ x y) (- x y)))
```


<a id="orga070630"></a>

## `defvar`

`(defvar variable-name type [value])`

This special form declares and optionally assigns a value to a variable.

Outside of a `defn` form, variables are stored in `storage` and accessible via `self.variable-name`.

Inside a `defn` form, variables are stored in `memory` and accessible directly.

The `value` form is optional.

```clojure
(defvar owner (public :address))
(defvar enabled :bool)

(defn foo [] :external
  (defvar owner_memory :address self/owner)) ;; declare copy in memory
```


<a id="org03a8bea"></a>

## `setv`

`(setv name value)`

This special form assigns a value to a name. It is roughly equivalent to the equal sign `=` in Vyper.

```clojure
;; Create a string variable that can store maximum 100 characters
(defvar greet (public (string 100)))

(defn __init__ [] :external
    (setv self/greet "Hello World")) ;; in vyper: self.greet = "Hello World"
```


<a id="orgcdd6191"></a>

## `definterface`

`(definterface name & fns)`

This special form declares an interface.

```clojure
(definterface TestInterface
  (defn owner [] :address :view)
  (defn setOwner [:address owner] :nonpayable)
  (defn sendEth [] :payable)
  (defn setOwnerAndSendEth [:address owner] :payable))
```


<a id="orga0f8171"></a>

## `defstruct`

`(defstruct name & variables)`

This special form declares a struct. Variables should be declared in pairs of `name` and `type`

```clojure
(defstruct Person
  name (string 100)
  age :uint256)
```


<a id="orgcdac4ec"></a>

## `defevent`

`(defevent name & fields)`

This special form declares an event. Fields should be declared in pairs of `name` and `type`

```clojure
(defevent Transfer
  sender (indexed :address)
  receiver (indexed :address)
  amount :uint256)
```


<a id="org9cbb6cd"></a>

## `/`

`(setv self/foo bar)`

Access object attributes. `obj/name` is shorthand for `(. obj name)`
