"""Backwards compatibility layer for parse functions.

This module provides versions of parse_node and parse_expr that can be called
without a context parameter for backwards compatibility.
"""

from .context import ParseContext
from typing import Optional

# Module-level context for backwards compatibility
_default_context: Optional[ParseContext] = None


def set_default_context(context: ParseContext) -> None:
    """Set the default context for backwards-compatible calls."""
    global _default_context
    _default_context = context


def get_default_context() -> ParseContext:
    """Get the default context, creating one if necessary."""
    global _default_context
    if _default_context is None:
        _default_context = ParseContext()
    return _default_context


def parse_node_compat(node):
    """Backwards-compatible version of parse_node."""
    from . import parse as parse_module

    return parse_module.parse_node(node, get_default_context())


def parse_expr_compat(expr):
    """Backwards-compatible version of parse_expr."""
    from . import parse as parse_module

    return parse_module.parse_expr(expr, get_default_context())
