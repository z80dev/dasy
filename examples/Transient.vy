#pragma evm-version cancun

@nonreentrant("lock")
@external
def foo() -> uint256:
    return 4
