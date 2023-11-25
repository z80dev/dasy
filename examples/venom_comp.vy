@external
def retOne() -> uint256:
    x: uint256 = 0
    x = 1
    return x


# 71 gas
@external
def addTwoNums(a: uint256, b: uint256) -> uint256:
    return a + b
