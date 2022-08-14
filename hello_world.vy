# Create a string variable that can store maximum 100 characters
greet: public(String[100])

@external
def __init__():
    self.greet = "Hello World"
