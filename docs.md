- [Current Status](#org9073914)
- [Syntax](#org5274328)
  - [Tuples](#orgead55ef)
  - [Arrays](#org1097fdb)
  - [Types](#org3f310a6)
- [Core Forms](#orgf8db2cd)
  - [`defn`](#orgf31ca64)
  - [`defvar`](#org513865e)
  - [`setv`](#org6daef4b)
  - [`definterface`](#org9ebd17e)
  - [`defstruct`](#orge6113fd)
  - [`defevent`](#org75ec200)
  - [`defconst`](#org704612d)
  - [`defmacro`](#org8a60145)
  - [`/`](#org5274fb3)



<a id="org9073914"></a>

# Current Status

Dasy is currently in pre-alpha. The language&rsquo;s core is still being designed and implemented.


<a id="org5274328"></a>

# Syntax

Dasy has a clojure-inspired lisp syntax with some influences from python. Some constructs are dasy-specific.


<a id="orgead55ef"></a>

## Tuples

Tuples are represented by a quoted list such as `'(1 2 3)`

The vyper equivalent is `(1, 2, 3)`


<a id="org1097fdb"></a>

## Arrays

Arrays are represented by a bracketed list, such as `[1 2 3]`

The vyper equivalent is `[1, 2, 3]`


<a id="org3f310a6"></a>

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


<a id="orgf8db2cd"></a>

# Core Forms


<a id="orgf31ca64"></a>

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


<a id="org513865e"></a>

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


<a id="org6daef4b"></a>

## `setv`

`(setv name value)`

This special form assigns a value to a name. It is roughly equivalent to the equal sign `=` in Vyper.

```clojure
;; Create a string variable that can store maximum 100 characters
(defvar greet (public (string 100)))

(defn __init__ [] :external
    (setv self/greet "Hello World")) ;; in vyper: self.greet = "Hello World"
```


<a id="org9ebd17e"></a>

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


<a id="orge6113fd"></a>

## `defstruct`

`(defstruct name & variables)`

This special form declares a struct. Variables should be declared in pairs of `name` and `type`

```clojure
(defstruct Person
  name (string 100)
  age :uint256)
```


<a id="org75ec200"></a>

## `defevent`

`(defevent name & fields)`

This special form declares an event. Fields should be declared in pairs of `name` and `type`

```clojure
(defevent Transfer
  sender (indexed :address)
  receiver (indexed :address)
  amount :uint256)
```


<a id="org704612d"></a>

## `defconst`

`(defconst name value)`

This special form declares a constant. The value must be provided when defined. This value can never change.

```clojure
(defconst MIN_AMT 100)
(defconst GREETING "Hello")
```


<a id="org8a60145"></a>

## `defmacro`

`(defmacro name args & body)`

This special form declares a macro. Macros are functions that run at compile time. Their inputs are code, and their outputs are code. They transform your code as it is built.

Macros can be used to implement convenient shorthand syntaxes. They can also be used to pull in information from the outside world into your contract at build time.

In the most simple terms, macros allow you to extend the Dasy compiler yourself in whichever way you see fit.

```clojure
;; (set-at myArr 0 100) -> (setv (subscript myArr 0) 100)
(defmacro set-at [array index new-val] `(setv (subscript ~array ~index) ~new-val))

;; (doto obj (.append 10) (.append 20)) -> (do (.append obj 10) (.append obj 20))
(defmacro doto [ obj #*cmds]
  (lfor c cmds
        `(~(get c 0) ~obj ~@(cut c 1 None))))
```


<a id="org5274fb3"></a>

## `/`

`(setv self/foo bar)`

Access object attributes. `obj/name` is shorthand for `(. obj name)`
