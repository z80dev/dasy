@external
def retOne() -> uint256:
    return 1


@external
def addTwoNums(a: uint256, b: uint256) -> uint256:
    return unsafe_add(a, b)
