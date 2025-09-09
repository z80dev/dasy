- [Hello World](#orgab104e1)
- [Data Types - Values](#orgdfdb8d3)
- [Data Types - References](#orgf9cd3a1)
- [Dynamic Arrays](#org35e30a0)
- [Functions](#org2ab743a)
- [Internal and External Functions](#org8c1b980)
- [View and Pure Functions](#orgba4049c)
- [Constructor](#orge3eecd9)
- [Private and Public State Variables](#org8273a91)
- [Constants](#orgbd0900e)
- [Immutable](#org5e764a4)
- [If/Else](#orgec4103d)
- [For Loop](#org2665dcc)
- [Errors](#org2223378)
- [Events](#org988b4c5)
- [Payable](#org20aaaff)
- [Default Function](#orge23c5a9)
- [Send Ether](#orga2f7ce2)
- [Raw Call](#org8c71915)
- [Delegate Call](#org5a607a3)
- [Interface](#org46151b1)
- [Hash Function](#orgdaa5d01)
- [Re-Entrancy Lock](#org1b506f7)
- [Self Destruct](#org0108c1e)



<a id="orgab104e1"></a>

# Hello World

```clojure
1  ;; Create a string variable that can store maximum 100 characters
2  (defvar greet (public (string 100)))
3  
4  (defn __init__ [] :external
5      (set self/greet "Hello World"))
```


<a id="orgdfdb8d3"></a>

# Data Types - Values

```clojure
 1  (defvars
 2      b (public :bool)
 3      i (public :int128)
 4      u (public :uint256)
 5      addr (public :address)
 6      b32 :bytes32
 7      bs (public (bytes 100))
 8      s   (public (string 100)))
 9  
10  (defn __init__ [] :external
11      (set self/b False)
12      (set self/i -1)
13      (set self/u 123)
14      (set self/b32 0xada1b75f8ae9a65dcc16f95678ac203030505c6b465c8206e26ae84b525cdacb)
15      (set self/bs b"\x01")
16      (set self/s "Hello Dasy"))
```


<a id="orgf9cd3a1"></a>

# Data Types - References

```clojure
 1  (defstruct Person
 2    name (string 100)
 3    age :uint256)
 4  
 5  (defvars
 6      nums (public (array :uint256 10)) ;; fixed size list, must be bounded
 7      myMap (public (hash-map :address :uint256))
 8      person (public Person))
 9  
10  (defn __init__ [] :external
11    (doto self/nums
12          (set-at 0 123) ;; this updates self.nums[0]
13          (set-at 9 456)) ;; this updates self.nums[9]
14  
15    ;; copies self.nums to array in memory
16    (defvar arr (array :uint256 10) self/nums)
17    (set-at arr 0 123) ;; does not modify self/nums
18  
19    ;; this updates self/myMap
20    (doto self/myMap
21          (set-at msg/sender 1) ;; self.myMap[msg.sender] = 1
22          (set-at msg/sender 11)) ;; self.myMap[msg.sender] = 11
23  
24    ;; this updates self/person
25    (doto self/person
26          (set-in age 11)
27          (set-in name "Dasy"))
28  
29    ;; you could put defvar inside a doto like the arr example
30    ;; above, but I don't think that is very readable
31    ;; doing it this way is clearer, leaving the defvar out of doto
32    ;; Person struct is copied into memory
33    (defvar p Person self/person)
34    (set-in p name "Solidity"))
```


<a id="org35e30a0"></a>

# Dynamic Arrays

```clojure
 1  ;; dynamic array of type uint256, max 3 elements
 2  (defvar nums (public (dyn-array :uint256 3)))
 3  
 4  (defn __init__ [] :external
 5    (doto self/nums
 6      (.append  11)
 7      (.append  22)
 8      (.append  33)
 9     ;; this will revert, appending to array with max 3 elements
10     ;; (.append self/nums 44)
11      )
12    ;; delete all elements
13    (set self/nums [])
14    ;; set values
15    (set self/nums [1 2 3]))
16  
17  (defn examples [(dyn-array :uint256 5) xs] (dyn-array :uint256 8) [:external :pure]
18    (defvar ys (dyn-array :uint256 8) [1 2 3])
19    (for [x xs]
20         (.append ys x))
21    (return ys))
22  
23  (defn filter [(dyn-array :address 5) addrs] (dyn-array :address 5) [:external :pure]
24    (defvar nonzeros (dyn-array :address 5) [])
25    (for [addr addrs]
26         (if (!= addr (empty :address))
27             (do (.append nonzeros addr))))
28    (return nonzeros))
```


<a id="org2ab743a"></a>

# Functions

```clojure
 1  (defn multiply [:uint256 x y] :uint256 [:external :pure]
 2    (* x y))
 3  
 4  (defn divide [:uint256 x y] :uint256 [:external :pure]
 5    (/ x y))
 6  
 7  (defn multiOut [] '(:uint256 :bool) [:external :pure]
 8    '(1 True))
 9  
10  (defn addAndSub [:uint256 x y] '(:uint256 :uint256) [:external :pure]
11    '((+ x y) (- x y)))
```


<a id="org8c1b980"></a>

# Internal and External Functions

```clojure
 1  ;; internal functions can only be called inside this contract
 2  (defn _add [:uint256 x y] :uint256 [:internal :pure]
 3    (+ x y))
 4  
 5  ;; external functions can only be called from outside this contract
 6  (defn extFunc [] :bool [:external :view]
 7    True)
 8  
 9  ;; external functions can only be called from outside this contract
10  (defn avg [:uint256 x y] :uint256 [:external :view]
11    ;; cannot call other external function
12    ;; (.extFunc self)
13  
14    ;; can call internal functions
15    (defvar z :uint256 (self/_add x y))
16    (/ (+ x y)
17       2))
18  
19  (defn _sqr [:uint256 x] :uint256 [:internal :pure]
20    (* x x))
21  
22  (defn sumOfSquares [:uint256 x y] :uint256 [:external :view]
23    (+ (self/_sqr x)
24       (self/_sqr y)))
```


<a id="orgba4049c"></a>

# View and Pure Functions

```clojure
 1  (defvar num (public :uint256))
 2  
 3  ;; Pure functions do not read any state or global variables
 4  (defn pureFunc [:uint256 x] :uint256 [:external :pure]
 5    x)
 6  
 7  ;; View functions might read state or global state, or call an internal function
 8  (defn viewFunc [:uint256 x] :bool [:external :view]
 9    (> x self/num))
10  
11  (defn sum [:uint256 x y z] :uint256 [:external :pure]
12    (+ x  y z))
13  
14  (defn addNum [:uint256 x] :uint256 [:external :view]
15    (+ x self/num))
```


<a id="orge3eecd9"></a>

# Constructor

```clojure
 1  (defvars owner (public :address)
 2          createdAt (public :uint256)
 3          expiresAt (public :uint256)
 4          name (public (string 10)))
 5  
 6  (defn __init__ [(string 10) name :uint256 duration] :external
 7      ;; set owner to caller
 8      (set self/owner msg/sender)
 9      ;; set name from input
10      (set self/name name)
11      (set self/createdAt block/timestamp)
12      (set self/expiresAt (+ block/timestamp
13                              duration)))
```


<a id="org8273a91"></a>

# Private and Public State Variables

```clojure
1  (defvars
2      owner (public :address)
3      foo :uint256
4      bar (public :bool))
5  
6  (defn __init__ [] :external
7    (set self/owner msg/sender)
8    (set self/foo 123)
9    (set self/bar True))
```


<a id="orgbd0900e"></a>

# Constants

```clojure
 1  (defconst MY_CONSTANT 123)
 2  (defconst MIN 1)
 3  (defconst MAX 10)
 4  (defconst ADDR 0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B)
 5  
 6  (defn getMyConstants [] '(:uint256 :uint256 :address) [:external :pure]
 7    '(MIN MAX ADDR))
 8  
 9  (defn test [:uint256 x] :uint256 [:external :pure]
10    (+ x MIN))
```


<a id="org5e764a4"></a>

# Immutable

```clojure
1  (defvar OWNER (immutable :address))
2  (defvar MY_IMMUTABLE (immutable :uint256))
3  
4  (defn __init__ [:uint256 _val] :external
5    (set OWNER msg/sender)
6    (set MY_IMMUTABLE _val))
7  
8  (defn getMyImmutable [] :uint256 [:external :pure]
9    MY_IMMUTABLE)
```


<a id="orgec4103d"></a>

# If/Else

```clojure
 1  (defn ifElse [:uint256 x] :uint256 :external
 2    (if (<= x 10)
 3        (return 1)
 4        (if (<= x 20)
 5            (return 2)
 6            (return 3))))
 7  
 8  (defn absoluteValue [:uint256 x y] :uint256 [:external :pure]
 9    (if (>= x y)
10        (return (- x y)))
11    (return (- y x)))
```


<a id="org2665dcc"></a>

# For Loop

```clojure
 1  (defn forLoop [] :uint256 [:external :pure]
 2    (defvar s :uint256 0)
 3    (for [i (range 10)]
 4         (+= s i))
 5    ;; for loop through array elements
 6    ;; find minimum of nums
 7    (defvar nums (array :uint256 5) [4 5 1 9 3])
 8    (defvar x :uint256 (max_value :uint256))
 9    (for [num nums]
10         (if (< num x)
11             (set x num)))
12    (defvar c :uint256 0)
13    (for [i [1 2 3 4 5]]
14         (if (== i 2)
15             (continue))
16         (if (== i 4)
17             (break))
18         (+= c 1))
19    c)
20  
21  (defn sum [(array :uint256 10) nums] :uint256 [:external :pure]
22    (defvar s :uint256 0)
23    (for [n nums]
24         (+= s n))
25    s)
```


<a id="org2223378"></a>

# Errors

```clojure
 1  (defvars
 2      x (public :uint256)
 3      owner (public :address))
 4  
 5  (defn __init__ [] :external
 6    (set self/owner msg/sender))
 7  
 8  (defn testAssert [:uint256 x] :external
 9    (assert (>= x 1) "x < 1")
10    (set self/x x))
11  
12  (defn testRaise [:uint256 x] :external
13    (if (<= x 1)
14        (raise "x < 1"))
15    (set self/x x))
16  
17  (defn _testErrorBubblesUp [:uint256 x] :internal
18    (assert (>= x 1) "x < 1")
19    (set self/x x))
20  
21  (defn testErrorBubblesUp [:uint256 x] :external
22    (self/_testErrorBubblesUp x)
23    (set self/x 123))
24  
25  (defn setOwner [:address owner] :external
26    (assert (== msg/sender self/owner) "!owner")
27    (assert (!= owner (empty :address)) "owner = zero")
28    (set self/owner owner))
```


<a id="org988b4c5"></a>

# Events

```clojure
 1  (defevent Transfer
 2    sender (indexed :address)
 3    receiver (indexed :address)
 4    amount :uint256)
 5  
 6  (defn transfer [:address receiver :uint256 amount] :external
 7    (log (Transfer :sender msg/sender :receiver receiver :amount amount)))
 8  
 9  (defn mint [:uint256 amount] :external
10    (log (Transfer :sender (empty :address) :receiver msg/sender :amount amount)))
11  
12  (defn burn [:uint256 amount] :external
13    (log (Transfer :sender msg/sender :receiver (empty :address) :amount amount)))
```


<a id="org20aaaff"></a>

# Payable

```clojure
 1  (defevent Deposit
 2    sender (indexed :address)
 3    amount :uint256)
 4  
 5  (defn deposit [] [:external :payable]
 6    (log (Deposit :sender msg/sender :amount msg/value)))
 7  
 8  (defn getBalance [] :uint256 [:external :view]
 9    ;; get balance of Ether stored in this contract
10    self/balance)
11  
12  (defvar owner (public :address))
13  
14  (defn pay [] [:external :payable]
15    (assert (> msg/value 0) "msg.value = 0")
16    (set self/owner msg/sender))
```


<a id="orge23c5a9"></a>

# Default Function

```clojure
1  (defevent Payment
2    sender (indexed :address)
3    amount :uint256)
4  
5  (defn __default__ [] [:external :payable]
6    (log (Payment :sender msg/sender :amount msg/value)))
```


<a id="orga2f7ce2"></a>

# Send Ether

```clojure
 1  ;; receive ether into the contract
 2  (defn __default__ [] [:external :payable]
 3    (pass))
 4  
 5  (defn sendEther [:address to :uint256 amount] :external
 6    ;; calls the default fn in the receiving contract
 7    (send to amount))
 8  
 9  (defn sendAll [:address to] :external
10    (send to self/balance))
```


<a id="org8c71915"></a>

# Raw Call

```clojure
 1  (defn testRawCall [:address to :uint256 x y] :uint256 :external
 2    (defvar res (bytes 32)
 3      (raw_call to
 4                (concat (method_id "multiply(uint256,uint256)")
 5                           (convert x :bytes32)
 6                           (convert y :bytes32))
 7                :max_outsize 32
 8                :gas 100000
 9                :value 0
10                ))
11    (defvar z :uint256 (convert res :uint256))
12    z)
13  
14  (defn sendEth [:address to] [:external :payable]
15    (raw_call to b"" :value msg/value))
```


<a id="org5a607a3"></a>

# Delegate Call

```clojure
1  (defvars x (public :uint256)
2           y (public :uint256))
3  
4  (defn updateX [:uint256 x] :external
5    (set self/x (+ x 1)))
6  
7  (defn updateY [:uint256 y] :external
8    (set self/y (* y y)))
```

```clojure
 1  (defvars x (public :uint256)
 2           y (public :uint256))
 3  
 4  (defn updateX [:address to :uint256 x] :external
 5    (raw_call to
 6              (concat
 7               (method_id "updateX(uint256)")
 8               (convert x :bytes32))
 9              :is_delegate_call True))
10  
11  (defn updateY [:address to :uint256 y] :external
12    (raw_call to
13              (concat
14               (method_id "updateY(uint256)")
15               (convert y :bytes32))
16              :is_delegate_call True))
```


<a id="org46151b1"></a>

# Interface

```clojure
 1  (definterface TestInterface
 2    (defn owner [] :address :view)
 3    (defn setOwner [:address owner] :nonpayable)
 4    (defn sendEth [] :payable)
 5    (defn setOwnerAndSendEth [:address owner] :payable))
 6  
 7  (defvar test (public TestInterface))
 8  
 9  (defn __init__ [:address test] :external
10    (set self/test (TestInterface test)))
11  
12  (defn getOwner [] :address [:external :view]
13    (.owner self/test))
14  
15  (defn getOwnerFromAddress [:address test] :address [:external :view]
16    (.owner (TestInterface test)))
17  
18  (defn setOwner [:address owner] :external
19    (.setOwner self/test owner))
```

```clojure
 1  (defvars
 2      owner (public :address)
 3      eth (public :uint256))
 4  
 5  (defn setOwner [:address owner] :external
 6    (set self/owner owner))
 7  
 8  (defn sendEth [] [:external :payable]
 9    (set self/eth msg/value))
10  
11  (defn setOwnerAndSendEth [:address owner] [:external :payable]
12    (set self/owner owner)
13    (set self/eth msg/value))
```


<a id="orgdaa5d01"></a>

# Hash Function

```clojure
1  (defn getHash [:address addr :uint256 num] :bytes32 [:external :pure]
2    (keccak256
3     (concat
4      (convert addr :bytes32)
5      (convert num :bytes32)
6      (convert "THIS IS A STRING" (bytes 16)))))
7  
8  (defn getMessageHash [(string 100) _str] :bytes32 [:external :pure]
9    (keccak256 _str))
```


<a id="org1b506f7"></a>

# Re-Entrancy Lock

```clojure
1  (defn func0 [] [:external (nonreentrant "lock")]
2    (raw_call msg/sender b"" :value 0))
3  
4  (defn func1 [] [:external (nonreentrant "lock-2")]
5    (raw_call msg/sender b"" :value 0))
6  
7  (defn func2 [] [:external (nonreentrant "lock-2")]
8    (raw_call msg/sender b"" :value 0))
```


<a id="org0108c1e"></a>

# Self Destruct

Deprecated in EVM/Vyper. The opcode is no longer recommended and may be removed.
Dasy intentionally avoids examples using `selfdestruct` to prevent compiler warnings.
