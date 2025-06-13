#!/usr/bin/env python
import logging
import sys
from dasy.compiler import generate_compiler_data

# Configure logging to show everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Simple test contract
src = """
(defn get-x [] :uint256 :external
  10)
"""

print("Compiling Dasy source:")
print(src)
print("-" * 40)

try:
    data = generate_compiler_data(src, "TestContract")
    print("Compilation successful!")
    print(f"Bytecode: {data.bytecode.hex()[:60]}...")
except Exception as e:
    print(f"Compilation failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()