#!/usr/bin/env python
import logging
from dasy.compiler import generate_compiler_data

# Configure logging
logging.basicConfig(level=logging.INFO)

# Test integer division
src = """
(defn divide-ints [:uint256 a :uint256 b] :uint256 :external
  (// a b))
"""

print("Testing integer division:")
print(src)
print("-" * 40)

try:
    data = generate_compiler_data(src, "TestDivision")
    print("Compilation successful!")
    print(f"ABI: {data.abi}")
except Exception as e:
    print(f"Compilation failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()