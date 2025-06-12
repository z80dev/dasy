"""
DasyReader - Custom Hy reader for Dasy language
Extends HyReader to handle 0x literals as symbols instead of integers
"""

import hy
from hy.reader.hy_reader import HyReader, as_identifier as hy_as_identifier
from hy import models


class DasyReader(HyReader):
    """Custom Hy reader that treats 0x prefixed values as symbols."""
    
    def __init__(self, **kwargs):
        # First call parent init to set up the basic reader
        super().__init__(**kwargs)
        # The parent __init__ will have set self.reader_table from the empty DEFAULT_TABLE
        # So we need to manually copy the parent's reader table
        self.reader_table = HyReader.DEFAULT_TABLE.copy()
        # Then apply any reader macro transformations
        self.reader_macros = {}
        for tag in list(self.reader_table.keys()):
            if tag[0] == '#' and tag[1:]:
                self.reader_macros[tag[1:]] = self.reader_table.pop(tag)
    
    def read_default(self, key):
        """Override to handle 0x literals as symbols instead of integers."""
        ident = key + self.read_ident()
        
        # Check for string prefix (like r"...")
        if self.peek_and_getc('"'):
            return self.prefixed_string('"', ident)
        
        # Handle 0x literals as symbols for Ethereum addresses
        # Ethereum addresses are exactly 42 characters: 0x + 40 hex chars
        if ident.startswith("0x") and len(ident) == 42:
            # Verify it's all valid hex characters after 0x
            try:
                int(ident[2:], 16)
                return models.Symbol(ident, from_parser=True)
            except ValueError:
                # Not valid hex, let normal parsing handle it
                pass
        
        # Otherwise use standard identifier parsing
        return hy_as_identifier(ident, reader=self)


def read_many(src, filename="<string>"):
    """
    Read multiple Dasy forms from source text using DasyReader.
    """
    return list(hy.read_many(src, filename=filename, reader=DasyReader()))


def read(src, filename="<string>"):
    """
    Read a single Dasy form from source text using DasyReader.
    """
    return hy.read(src, filename=filename, reader=DasyReader())