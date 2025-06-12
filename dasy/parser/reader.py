"""
DasyReader - Custom Hy reader for Dasy language
Extends HyReader to handle 0x literals as symbols instead of integers
"""

import hy
from hy.reader import hy_reader
from hy.reader.hy_reader import HyReader
from hy import models


# Save the original as_identifier function
_original_as_identifier = hy_reader.as_identifier


def dasy_as_identifier(ident, reader=None):
    """
    Custom identifier parser that treats 0x prefixed values as symbols
    instead of integers.
    """
    # Check if this is a hex literal
    if isinstance(ident, str) and ident.startswith("0x"):
        # Return as a Symbol instead of trying to parse as Integer
        # Use from_parser=True to bypass validation
        return models.Symbol(ident, from_parser=True)
    
    # Otherwise, use the default Hy behavior
    return _original_as_identifier(ident, reader)


# Monkey-patch the module-level function
hy_reader.as_identifier = dasy_as_identifier


def read_many(src, filename="<string>"):
    """
    Read multiple Dasy forms from source text.
    The as_identifier function has been monkey-patched to handle 0x literals.
    """
    # Just use hy.read_many since we've patched as_identifier
    return list(hy.read_many(src, filename=filename))


def read(src, filename="<string>"):
    """
    Read a single Dasy form from source text.
    The as_identifier function has been monkey-patched to handle 0x literals.
    """
    # Just use hy.read since we've patched as_identifier
    return hy.read(src, filename=filename)