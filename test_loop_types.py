#!/usr/bin/env python
import logging
from dasy.compiler import generate_compiler_data

# Configure logging
logging.basicConfig(level=logging.INFO)

# Test loop with type annotation
src_new = """
(defn sum-range [] :uint256 :external
  (defvar s :uint256 0)
  (for [i :uint256 (range 10)]
    (+= s i))
  s)
"""

# Test old loop syntax (should still work for backward compatibility)
src_old = """
(defn sum-range-old [] :uint256 :external
  (defvar s :uint256 0)
  (for [i (range 10)]
    (+= s i))
  s)
"""

print("Testing NEW loop syntax with type annotation:")
print(src_new)
print("-" * 40)

try:
    data = generate_compiler_data(src_new, "TestLoop")
    print("New syntax compilation successful!")
    print(f"ABI function: {data.abi[0]['name']}")
except Exception as e:
    print(f"New syntax compilation failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60 + "\n")

print("Testing OLD loop syntax (backward compatibility):")
print(src_old)
print("-" * 40)

try:
    data = generate_compiler_data(src_old, "TestLoop")
    print("Old syntax compilation successful!")
    print(f"ABI function: {data.abi[0]['name']}")
except Exception as e:
    print(f"Old syntax compilation failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()