- [Current Status](#org8cc4f22)
- [Syntax](#org965f6a0)
  - [Tuples](#orgd4c2ce3)
- [Core Macros](#org0abdab9)
  - [`defn`](#org804db0a)
  - [`defvar`](#org06c726e)
  - [`setv`](#org71e9681)
  - [`definterface`](#orgd06a087)
  - [`defstruct`](#orgbe9dae8)
  - [`defevent`](#org1e5dab2)
  - [`/`](#org79c18a4)



<a id="org8cc4f22"></a>

# Current Status

Dasy is currently in pre-alpha. The language&rsquo;s core is still being designed and implemented.


<a id="org965f6a0"></a>

# Syntax

Dasy has a clojure-inspired lisp syntax with some influences from python. Some constructs are dasy-specific.


<a id="orgd4c2ce3"></a>

## Tuples

Tuples are signified by a quoted list such as `'(1 2 3)` The vyper equivalent is `(1, 2, 3)`


<a id="org0abdab9"></a>

# Core Macros


<a id="org804db0a"></a>

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


<a id="org06c726e"></a>

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


<a id="org71e9681"></a>

## `setv`

`(setv name value)`

This special form assigns a value to a name. It is roughly equivalent to the equal sign `=` in Vyper.

```clojure
;; Create a string variable that can store maximum 100 characters
(defvar greet (public (string 100)))

(defn __init__ [] :external
    (setv self/greet "Hello World")) ;; in vyper: self.greet = "Hello World"
```


<a id="orgd06a087"></a>

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


<a id="orgbe9dae8"></a>

## `defstruct`

`(defstruct name & variables)`

This special form declares a struct. Variables should be declared in pairs of `name` and `type`

```clojure
(defstruct Person
  name (string 100)
  age :uint256)
```


<a id="org1e5dab2"></a>

## `defevent`

`(defevent name & fields)`

This special form declares an event. Fields should be declared in pairs of `name` and `type`

```clojure
(defevent Transfer
  sender (indexed :address)
  receiver (indexed :address)
  amount :uint256)
```


<a id="org79c18a4"></a>

## `/`

`(setv self/foo bar)`

Access object attributes. `obj/name` is shorthand for `(. obj name)`
