import dasy
import hy
from boa.contract import VyperContract
import boa

def get_contract(src: str, *args) -> VyperContract:
    return VyperContract(dasy.compile(src), *args)


def test_binops():
    src = """
        (defn plus [] :uint256 :external
        (+ 1 2))
    """
    c = get_contract(src)
    assert c.plus() == 3

def test_chain_binops():
    src = """
        (defn plus [] :uint256 :external
        (+ 1 2 3 4 5 6))
    """
    c = get_contract(src)
    assert c.plus() == 21

def test_defvar():
    src = """
    (defvar x :uint256)
    (defn setX [:uint256 x] :external
      (setv self/x x))
    (defn getX [] :uint256 [:external :view] self/x)
    """
    c = get_contract(src)
    c.setX(10)
    assert c.getX() == 10

def test_hello_world():
    c = get_contract("""
    (defvar greet (public (:string 100)))
    (defn __init__ [] :external (setv self/greet "Hello World"))
    (defn setGreet [(:string 100) x] :external (setv self/greet x))
    """)
    assert c.greet() == "Hello World"
    c.setGreet("yo yo")
    assert c.greet() == "yo yo"

def test_call_internal():
    c = get_contract("""
    (defn _getX [] :uint256 :internal 4)
    (defn useX [] :uint256 :external
      (+ 2 (self/_getX)))
    """)
    assert c.useX() == 6

def test_pure_fn():
    c = get_contract("""
    (defn pureX [:uint256 x] :uint256 [:external :pure] x)
    """)
    assert c.pureX(6) == 6

def test_constructor():
    c = get_contract("""
    (defvar owner (public :address)
            createdAt (public :uint256)
            expiresAt (public :uint256)
            name (public (:string 10)))
    (defn __init__ [:uint256 duration] :external
      (setv self/owner msg/sender)
      (setv self/name "z80")
      (setv self/createdAt block/timestamp)
      (setv self/expiresAt (+ block/timestamp
                              duration)))
    """, 100)

    createdAt = c.createdAt()
    expiresAt = c.expiresAt()
    assert expiresAt == createdAt + 100
    assert c.name() == "z80"

def test_if():
    c = get_contract("""
    (defn absValue [:uint256 x y] :uint256 [:external :pure]
      (if (>= x y)
         (return (- x y))
         (return (- y x))))""")
    assert c.absValue(4, 7) == 3

def test_struct():
    c = get_contract("""
    (defstruct Person
        age :uint256)
    (defvar person (public Person))
    (defn __init__ [] :external
      )
    """)
    assert c.person()[0] == 0
