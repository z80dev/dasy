#!/usr/bin/env python
import logging
from dasy.compiler import generate_compiler_data

# Configure logging
logging.basicConfig(level=logging.INFO)

# Test module system - uses declaration
src_uses = """
;; Import a module
(uses math)

(defn calculate [:uint256 x] :uint256 :external
  (math.sqrt x))
"""

# Test module system - initializes
src_initializes = """
;; Initialize a module
(initializes math)

(defn __init__ [] :deploy
  (math.__init__))
"""

# Test module system - exports
src_exports = """
;; Export a function
(defn helper [:uint256 x] :uint256 :internal
  (* x x))

(exports helper)
"""

print("Testing module 'uses' declaration:")
print(src_uses)
print("-" * 40)

try:
    data = generate_compiler_data(src_uses, "TestUses")
    print("Uses compilation successful!")
except Exception as e:
    print(f"Uses compilation failed: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60 + "\n")

print("Testing module 'initializes' declaration:")
print(src_initializes)
print("-" * 40)

try:
    data = generate_compiler_data(src_initializes, "TestInitializes")
    print("Initializes compilation successful!")
except Exception as e:
    print(f"Initializes compilation failed: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60 + "\n")

print("Testing module 'exports' declaration:")
print(src_exports)
print("-" * 40)

try:
    data = generate_compiler_data(src_exports, "TestExports")
    print("Exports compilation successful!")
except Exception as e:
    print(f"Exports compilation failed: {type(e).__name__}: {str(e)}")