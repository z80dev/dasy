from __future__ import annotations

"""
Vyper compatibility helpers for 0.4.x.

This module centralizes imports and construction of Vyper compiler objects that
sometimes move between minor releases. Keep all version-aware logic here to
avoid ad-hoc patches elsewhere.
"""

from pathlib import Path
from typing import Optional

from vyper.compiler.phases import CompilerData as VyperCompilerData
from vyper.compiler.input_bundle import FileInput
from vyper.compiler.settings import Settings


def make_file_input(src: str, name: str, filepath: Optional[str]) -> FileInput:
    """Create a Vyper FileInput for the given source.

    - filepath is attached to both `path` and `resolved_path` if provided, else
      a default `<name>.dasy` placeholder is used.
    - source_id is set to 0 for single-file compilation.
    """
    path = filepath or f"{name}.dasy"
    return FileInput(
        contents=src,
        source_id=0,
        path=path,
        resolved_path=path,
    )


def make_compiler_data(file_input: FileInput, settings: Settings) -> VyperCompilerData:
    """Return a Vyper CompilerData instance for a single input file.

    Note: For single-file usage, pass the FileInput directly rather than string
    source. This avoids internal API churn across minor versions.
    """
    return VyperCompilerData(file_input, settings=settings)

