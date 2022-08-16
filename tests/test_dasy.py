import dasy
from boa.contract import VyperContract

def get_contract(src: str) -> VyperContract:
    return VyperContract(dasy.compile(src))

def test_chain_binops():
    src = """
    (defcontract test []
        (defn foo [] :uint256 :external
        (+ 1 2 3)))
    """
    c = get_contract(src)
    assert c.foo() == 6
