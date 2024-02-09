#pragma evm-version cancun

@nonreentrant("lock")
@external
def func0():
    raw_call(msg.sender, b"", value=0)
