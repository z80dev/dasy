a: bool
b: bool
cap: public(uint256)

@external
def checkA() -> bool:
    if self.cap < 100:
        return self.cap
    else:
        return 100
