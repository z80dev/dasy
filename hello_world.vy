base: public(uint256)

@external
def set_base(x: uint256):
    self.base = x

@external
def foo(x: uint256) -> (uint256, uint256):
    return 4, 7
