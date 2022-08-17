import dasy
import hy
from boa.contract import VyperContract

def get_contract(src: str) -> VyperContract:
    return VyperContract(dasy.compile(src))


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
        (+ 1 2 3))
    """
    c = get_contract(src)
    assert c.plus() == 6

def test_defvar():
    src = """
    (defvar x :uint256)
    (defn setX [:uint256 x] :external (setv self/x x))
    (defn getX [] :uint256 :external self/x)
    """
    c = get_contract(src)
    c.setX(10)
    assert c.getX() == 10
