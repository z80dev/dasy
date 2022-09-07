
# Table of Contents

1.  [Current Status](#org7a0419e)
2.  [Syntax](#org0d3f35f)
    1.  [Tuples](#org0c572ec)
3.  [Core Macros](#org0eb66cf)
    1.  [`defn`](#orgaa3a527)
    2.  [`defvar`](#org6ac187c)
    3.  [`setv`](#orgf8b3d0c)
    4.  [`definterface`](#orga96a2f7)
    5.  [`defstruct`](#orge4aaa92)
    6.  [`defevent`](#org9c0fda7)
    7.  [`/`](#orgfc40cb1)



<a id="org7a0419e"></a>

# Current Status

Dasy is currently in pre-alpha. The language&rsquo;s core is still being designed and implemented.


<a id="org0d3f35f"></a>

# Syntax

Dasy has a clojure-inspired lisp syntax with some influences from python. Some constructs are dasy-specific.


<a id="org0c572ec"></a>

## Tuples

Tuples are signified by a quoted list such as `'(1 2 3)`
The vyper equivalent is `(1, 2, 3)`


<a id="org0eb66cf"></a>

# Core Macros


<a id="orgaa3a527"></a>

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

    (defn noArgs [] :external (pass))
    
    (defn setNum [:uint256 x] :external (pass))
    
    (defn addNums [:uint256 x y] :uint256 [:external :pure]
      (+ x y))
    
    (defn addAndSub [:uint256 x y] '(:uint256 :uint256) [:external :pure]
      '((+ x y) (- x y)))


<a id="org6ac187c"></a>

## `defvar`

`(defvar variable-name type [value])`

This special form declares and optionally assigns a value to a variable.

Outside of a `defn` form, variables are stored in `storage` and accessible via `self.variable-name`.

Inside a `defn` form, variables are stored in `memory` and accessible directly.

The `value` form is optional.

    (defvar owner (public :address))
    (defvar enabled :bool)
    
    (defn foo [] :external
      (defvar owner_memory :address self/owner)) ;; declare copy in memory


<a id="orgf8b3d0c"></a>

## `setv`

`(setv name value)`

This special form assigns a value to a name. It is roughly equivalent to the equal sign `=` in Vyper.

    ;; Create a string variable that can store maximum 100 characters
    (defvar greet (public (string 100)))
    
    (defn __init__ [] :external
        (setv self/greet "Hello World")) ;; in vyper: self.greet = "Hello World"


<a id="orga96a2f7"></a>

## `definterface`

`(definterface name & fns)`

This special form declares an interface.

    (definterface TestInterface
      (defn owner [] :address :view)
      (defn setOwner [:address owner] :nonpayable)
      (defn sendEth [] :payable)
      (defn setOwnerAndSendEth [:address owner] :payable))


<a id="orge4aaa92"></a>

## `defstruct`

`(defstruct name & variables)`

This special form declares a struct. Variables should be declared in pairs of `name` and `type`

    (defstruct Person
      name (string 100)
      age :uint256)


<a id="org9c0fda7"></a>

## `defevent`

`(defevent name & fields)`

This special form declares an event. Fields should be declared in pairs of `name` and `type`

    (defevent Transfer
      sender (indexed :address)
      receiver (indexed :address)
      amount :uint256)


<a id="orgfc40cb1"></a>

## `/`

`(setv self/foo bar)`

Access object attributes. `obj/name` is shorthand for `(. obj name)`

