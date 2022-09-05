import dasy
import hy
from boa.contract import VyperContract
import boa

def compile_src(src: str, *args) -> VyperContract:
    return VyperContract(dasy.compile(src), *args)

def compile(filename: str, *args) -> VyperContract:
    with open(filename) as f:
        src = f.read()
        return compile_src(src, *args)

def test_binops():
    src = """
        (defn plus [] :uint256 :external
        (+ 1 2))
    """
    c = compile_src(src)
    assert c.plus() == 3

def test_chain_binops():
    src = """
        (defn plus [] :uint256 :external
        (+ 1 2 3 4 5 6))
    """
    c = compile_src(src)
    assert c.plus() == 21

def test_defvars():
    src = """
    (defvars x :uint256)
    (defn setX [:uint256 x] :external
      (setv self/x x))
    (defn getX [] :uint256 [:external :view] self/x)
    """
    c = compile_src(src)
    c.setX(10)
    assert c.getX() == 10

def test_hello_world():
    c = compile_src("""
    (defvars greet (public (string 100)))
    (defn __init__ [] :external (setv self/greet "Hello World"))
    (defn setGreet [(string 100) x] :external (setv self/greet x))
    """)
    assert c.greet() == "Hello World"
    c.setGreet("yo yo")
    assert c.greet() == "yo yo"

def test_call_internal():
    c = compile_src("""
    (defn _getX [] :uint256 :internal 4)
    (defn useX [] :uint256 :external
      (+ 2 (self/_getX)))
    """)
    assert c.useX() == 6

def test_pure_fn():
    c = compile_src("""
    (defn pureX [:uint256 x] :uint256 [:external :pure] x)
    """)
    assert c.pureX(6) == 6

def test_constructor():
    c = compile("examples/constructor.dasy", "z80", 100)

    createdAt = c.createdAt()
    expiresAt = c.expiresAt()
    assert expiresAt == createdAt + 100
    assert c.name() == "z80"

def test_if():
    c = compile_src("""
    (defn absValue [:uint256 x y] :uint256 [:external :pure]
      (if (>= x y)
         (return (- x y))
         (return (- y x))))""")
    assert c.absValue(4, 7) == 3

def test_struct():
    c = compile_src("""
    (defstruct Person
        age :uint256)
    (defvars person (public Person))
    (defn __init__ [] :external
      (setv (. self/person age) 12))
    (defn memoryPerson [] Person :external
      (defvar mPers Person self/person)
      (set-in mPers age 10)
      mPers)
    """)
    assert c.person()[0] == 12
    assert c.memoryPerson() == (10,)

def test_arrays():
    c = compile_src("""
    (defvars nums (public (array :uint256 10)))
    (defn __init__ [] :external
      (doto self/nums
        (set-at 0 5)
        (set-at 1 10))
      )
    """)
    assert c.nums(0) == 5
    assert c.nums(1) == 10

def test_map():
    c = compile_src("""
    (defvars myMap (public (hash-map :address :uint256))
            owner (public :address))
    (defn __init__ [] :external
      (setv self/owner msg/sender)
      (set-at self/myMap msg/sender 10))
    (defn getOwnerNum [] :uint256 :external
     (get-in self/myMap msg/sender))
    """)
    assert c.myMap("0x8B4de256180CFEC54c436A470AF50F9EE2813dbB") == 0
    assert c.myMap(c.owner()) == 10
    assert c.getOwnerNum() == 10

def test_dynarrays():
    c = compile_src("""
    (defvar nums (public (dyn-array :uint256 3)))
    (defn __init__ [] :external
    (.append self/nums 11)
    (.append self/nums 12))
    """)
    assert c.nums(0) == 11
    assert c.nums(1) == 12


def test_reference_types():
    c = compile_src("""
    (defvar nums (array :uint256 10))
    (defn memoryArrayVal [] '(:uint256 :uint256) :external
      (defvar arr (array :uint256 10) self/nums)
      (set-at arr 1 12)
      '((get-in arr 0) (get-in arr 1)))
    """)
    assert c.memoryArrayVal() == (0, 12)

    d = compile("examples/reference_types.dasy")
    assert d.person() == ("Dasy", 11)
    assert d.nums(0) == 123
    assert d.nums(1) == 0
    assert d.nums(9) == 456

def test_dynarrays():
    c = compile("examples/dynamic_arrays.dasy")
    assert c.nums(0) == 1
    assert c.nums(1) == 2
    assert c.nums(2) == 3
    assert c.examples([9, 8, 7, 6, 5]) == (1, 2, 3, 9, 8, 7, 6, 5)

def test_expr_wrap():
    c = compile_src("""
    (defvar owner (public :address))
    (defvar nums (public (dyn-array :uint256 3)))
    (defn test [] :external
      (setv self/owner msg/sender)
      (.append self/nums 1))
    """)
    c.test()

def test_funtions():
    c = compile("examples/functions.dasy")
    assert c.multiply(5, 10) == 50
    assert c.divide(100, 10) == 10
    assert c.multiOut() == (1, True)
    assert c.addAndSub(50, 25) == (75, 25)

def test_visibility():
    c = compile("examples/function_visibility.dasy")
    assert c.extFunc() == True
    assert c.sumOfSquares(2, 5) == 29
    assert c.avg(20, 80) == 50

def test_view_pure():
    c = compile("examples/view_pure.dasy")
    assert c.pureFunc(5) == 5
    assert c.viewFunc(1) == True
    assert c.sum(4, 5, 6) == 15
    assert c.addNum(10) == 10

def test_constants():
    c = compile("examples/constants.dasy")
    assert c.getMyConstants() == (1, 10, "0xab5801a7d398351b8be11c439e05c5b3259aec9b")
    assert c.test(5) == 6
