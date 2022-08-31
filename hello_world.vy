struct Person:
    name: String[100]
    age: uint256


# Fixed sized list
nums: public(uint256[10])  # must be bounded
myMap: public(HashMap[address, uint256])
person: public(Person)


@external
def __init__():
    # This updates self.nums[0]
    self.nums[0] = 123
    self.nums[9] = 456
    # Copies self.nums to array in memory.
    # Does not modify referenced variable (self.nums)
    arr: uint256[10] = self.nums
    arr[0] = 123

    # This updates self.myMap
    self.myMap[msg.sender] = 1
    self.myMap[msg.sender] = 11

    # This updates self.person
    self.person.age = 11
    self.person.name = "Vyper"
    # Person struct is copied into memory.
    # Does not modify referenced variable (self.person)
    p: Person = self.person
    p.name = "Solidity"
