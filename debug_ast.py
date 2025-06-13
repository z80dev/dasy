#!/usr/bin/env python
import logging
import sys
from dasy.parser import parse_src

# Configure logging to show everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

# Simple test contract
src = """
(defn get-x [] :uint256 :external
  10)
"""

print("Parsing Dasy source:")
print(src)
print("-" * 40)

try:
    ast, settings = parse_src(src)
    
    print(f"AST type: {type(ast).__name__}")
    print(f"AST attributes: {[attr for attr in dir(ast) if not attr.startswith('_')]}")
    print(f"Body length: {len(ast.body)}")
    
    for i, node in enumerate(ast.body):
        print(f"\nBody[{i}]:")
        print(f"  Type: {type(node).__name__}")
        print(f"  Name: {getattr(node, 'name', 'N/A')}")
        print(f"  Args: {getattr(node, 'args', 'N/A')}")
        if hasattr(node, 'body'):
            print(f"  Body length: {len(node.body)}")
            for j, child in enumerate(node.body):
                print(f"    Body[{j}]: {type(child).__name__}")
                if hasattr(child, 'value'):
                    print(f"      Value: {child.value}")
                    print(f"      Value type: {type(child.value).__name__}")
                    if hasattr(child.value, 'value'):
                        print(f"        Inner value: {child.value.value}")
        
        # Check parent-child relationships
        if hasattr(node, '_parent'):
            print(f"  Parent: {type(node._parent).__name__ if node._parent else 'None'}")
        if hasattr(node, '_children'):
            print(f"  Children count: {len(node._children)}")
    
    print("\nSettings:", settings)
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()