#!/usr/bin/env python
import logging
from dasy.compiler import generate_compiler_data

# Configure logging
logging.basicConfig(level=logging.INFO)

# Test struct instantiation - current syntax
src_old = """
(defstruct Person
  name (string 100)
  age :uint256)

(defn create-person [] Person :external
  (Person {:name "Test" :age 42}))
"""

# Test struct instantiation - new keyword syntax
src_new = """
(defstruct Person
  name (string 100)
  age :uint256)

(defn create-person [] Person :external
  (Person :name "Test" :age 42))
"""

print("Testing OLD struct instantiation syntax:")
print(src_old)
print("-" * 40)

try:
    data = generate_compiler_data(src_old, "TestStruct")
    print("Old syntax compilation successful!")
except Exception as e:
    print(f"Old syntax compilation failed: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60 + "\n")

print("Testing NEW struct instantiation syntax:")
print(src_new)
print("-" * 40)

try:
    data = generate_compiler_data(src_new, "TestStruct")
    print("New syntax compilation successful!")
except Exception as e:
    print(f"New syntax compilation failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()