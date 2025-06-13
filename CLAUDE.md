# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dasy is an experimental smart contract programming language in the Lisp family that compiles to Vyper. It features:
- Clojure-inspired Lisp syntax with Python influences
- Macro system implemented in Hy (a pythonic Lisp)
- Compiles to Vyper for EVM deployment
- Benefits from Vyper's optimizations and security features

## Development Workflow Notes

- Use uv for all python related commands

## Common Development Commands

### Running Tests
```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_dasy.py

# Run a specific test
uv run pytest tests/test_dasy.py::test_hello_world
```

### Linting
```bash
# Format Python code with black
uv run black dasy/ tests/
```

### Building and Installing
```bash
# Install for development (creates .venv automatically)
uv sync

# Install with dev dependencies
uv sync --dev

# Install in editable mode (already handled by uv sync)
# uv automatically installs the project in editable mode
```

### Using the Dasy Compiler
```bash
# Compile a Dasy file to bytecode (default)
uv run dasy examples/hello_world.dasy

# Compile with specific output format
uv run dasy examples/hello_world.dasy -f abi
uv run dasy examples/hello_world.dasy -f vyper_interface

# Available output formats: bytecode, abi, vyper_interface, external_interface, ir, opcodes, etc.
```

## High-Level Architecture

### Compilation Pipeline
1. **Parser** (`dasy/parser/`): Parses Dasy source code using Hy
   - `parse.py`: Main parsing logic, converts Hy forms to Vyper AST nodes
   - `macros.py`: Handles macro expansion
   - `nodes.py`, `core.py`: Handle specific language constructs
   - `ops.py`: Handles operators and built-in functions

2. **Compiler** (`dasy/compiler.py`): Extends Vyper's CompilerData
   - Integrates with Vyper's compilation phases
   - Handles output generation for various formats

3. **Built-ins** (`dasy/builtin/`):
   - `functions.py`: Built-in function definitions
   - `macros.hy`: Built-in macros written in Hy

### Key Design Patterns

- **Macro System**: Macros are written in Hy and transform code at compile time
- **AST Transformation**: Dasy forms are parsed into Hy models, then transformed to Vyper AST nodes
- **Vyper Integration**: Leverages Vyper's compiler infrastructure for optimization and code generation

### Testing Infrastructure

- Tests use `titanoboa` for EVM simulation
- Test files in `tests/test_dasy.py` compile example contracts and verify their behavior
- Example contracts in `examples/` serve as both documentation and test cases

### Important Notes

- The project requires Python 3.10-3.11 (as specified in pyproject.toml)
- EVM version can be set via pragma in Dasy files
- The language is in pre-alpha - core language features are still being developed
