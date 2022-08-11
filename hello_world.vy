base: public(uint256)
base2: uint256

@external
def set_base(x: uint256):
    self.base = x

@external
def add_to_base(x: uint256):
    return x + self.base

@external
def foo(x: uint256) -> (uint256, uint256):
    return 4, 7
