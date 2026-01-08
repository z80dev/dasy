"""Test all code examples from README.md to ensure they compile correctly."""

import pytest
import dasy


class TestReadmeExamples:
    """Test examples from the README."""

    def test_hello_world(self):
        """Quick Start example."""
        src = """
(defvar greet (public (string 100)))

(defn __init__ [] :external
  (set self/greet "Hello World"))
"""
        dasy.compile(src)

    def test_syntax_comparison(self):
        """Why Dasy - syntax comparison example."""
        src = """
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
"""
        dasy.compile(src)

    def test_storage_variables(self):
        """Storage variables example."""
        src = """
;; Single storage variable
(defvar owner (public address))

;; Multiple storage variables with defvars
(defvars
  :public
  name (string 32)
  symbol (string 32)
  decimals uint8
  totalSupply uint256
  balanceOf (hash-map address uint256))

;; Private storage (omit :public)
(defvars
  _internalCounter uint256
  _adminList (dyn-array address 100))
"""
        dasy.compile(src)

    def test_local_variables(self):
        """Local variables example."""
        src = """
(defn example [] uint256 :external
  ;; Local variable with type annotation
  (defvar x uint256 10)

  ;; Local variable with initial value from expression
  (defvar y uint256 (* x 2))

  ;; Fixed array literal
  (defvar nums (array uint256 3) [1 2 3])

  y)
"""
        dasy.compile(src)

    def test_constants_immutables(self):
        """Constants and immutables example."""
        src = """
;; Compile-time constant
(defconst MAX_SUPPLY uint256 1000000)

;; Immutable (set once in constructor)
(defvar OWNER (immutable address))

(defn __init__ [] :external
  (set OWNER msg/sender))
"""
        dasy.compile(src)

    def test_function_syntax(self):
        """Function syntax examples."""
        src = """
(defvar owner (public address))
(defvar totalSupply (public uint256))
(defvar deposits (public uint256))

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
"""
        dasy.compile(src)

    def test_if_expressions(self):
        """If expressions example."""
        src = """
;; if returns a value
(defn absoluteValue [[x uint256] [y uint256]] uint256 [:external :pure]
  (if (>= x y)
      (- x y)
      (- y x)))
"""
        dasy.compile(src)

    def test_cond_multiway(self):
        """Cond multi-way branch example."""
        src = """
(defn classify [[x uint256]] uint256 :external
  (cond
    (< x 10)  1
    (< x 100) 2
    (< x 1000) 3
    :else     4))
"""
        dasy.compile(src)

    def test_for_loops(self):
        """For loop examples."""
        src = """
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
"""
        dasy.compile(src)

    def test_arrays(self):
        """Array examples."""
        src = """
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
"""
        dasy.compile(src)

    def test_hash_maps(self):
        """Hash map examples."""
        src = """
(defvar balances (public (hash-map address uint256)))
(defvar allowances (public (hash-map address (hash-map address uint256))))
(defvar spender (public address))

(defn mapOps [] :external
  ;; Get value
  (defvar bal uint256 (get-at self/balances msg/sender))

  ;; Set value
  (set-at self/balances msg/sender 100)

  ;; Nested map access
  (defvar allowed uint256 (get-at self/allowances msg/sender self/spender))
  (set-at self/allowances msg/sender self/spender 50))
"""
        dasy.compile(src)

    def test_structs(self):
        """Struct examples."""
        src = """
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
"""
        dasy.compile(src)

    def test_flags(self):
        """Flag (enum) examples."""
        src = """
(defflag Roles
  ADMIN
  USER
  MODERATOR)

(defvar userRoles (public (hash-map address Roles)))

(defn checkRole [] bool [:external :view]
  (== (get-at self/userRoles msg/sender) Roles/ADMIN))
"""
        dasy.compile(src)

    def test_events(self):
        """Event examples."""
        src = """
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
"""
        dasy.compile(src)

    def test_interfaces(self):
        """Interface definition example."""
        src = """
(definterface IERC20
  (defn totalSupply [] uint256 :view)
  (defn balanceOf [[owner address]] uint256 :view)
  (defn transfer [[to address] [amount uint256]] bool :nonpayable)
  (defn approve [[spender address] [amount uint256]] bool :nonpayable))
"""
        dasy.compile(src)

    def test_external_calls(self):
        """External calls example."""
        src = """
(definterface IERC20
  (defn totalSupply [] uint256 :view)
  (defn balanceOf [[owner address]] uint256 :view)
  (defn transfer [[to address] [amount uint256]] bool :nonpayable)
  (defn approve [[spender address] [amount uint256]] bool :nonpayable))

(defvar token (public IERC20))

(defn __init__ [[tokenAddr address]] :external
  (set self/token (IERC20 tokenAddr)))

;; staticcall for view/pure functions
(defn getTokenBalance [[owner address]] uint256 [:external :view]
  (staticcall (. self/token balanceOf owner)))

;; extcall for state-changing functions
(defn sendTokens [[to address] [amount uint256]] :external
  (extcall (. self/token transfer to amount)))
"""
        dasy.compile(src)

    def test_raw_calls(self):
        """Raw call example."""
        src = """
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
"""
        dasy.compile(src)

    def test_error_handling(self):
        """Error handling examples."""
        src = """
(defvar balances (hash-map address uint256))
(defvar owner address)

;; Assert with message
(defn withdraw [[amount uint256]] :external
  (assert (>= (get-at self/balances msg/sender) amount) "Insufficient balance")
  (assert (!= amount 0) "Amount must be non-zero"))

;; Raise (revert) with message
(defn onlyOwner [] :internal
  (if (!= msg/sender self/owner)
      (raise "Not authorized")))
"""
        dasy.compile(src)

    def test_infix_macro(self):
        """Custom macro example - infix."""
        src = """
;; Define an infix macro
(define-syntax infix
  (syntax-rules ()
    ((infix (a op b)) (op a b))))

;; Now you can write
(defn testInfix [[x uint256] [y uint256]] uint256 [:external :pure]
  (infix (x + y)))
"""
        dasy.compile(src)

    def test_erc20_complete(self):
        """Complete ERC20 example."""
        src = """
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
"""
        dasy.compile(src)

    def test_auction_complete(self):
        """Complete auction example."""
        src = """
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
"""
        dasy.compile(src)

    def test_titanoboa_example(self):
        """Titanoboa integration example."""
        src = """
(defvar value (public uint256))
(defn setValue [[v uint256]] :external
  (set self/value v))
"""
        dasy.compile(src)
