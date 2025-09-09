"""Thread-local storage for macro execution context."""

import threading
from typing import Optional
from .context import ParseContext

# Thread-local storage for the current parse context
_thread_local = threading.local()


def set_macro_context(context: ParseContext) -> None:
    """Set the current macro context for this thread."""
    _thread_local.context = context


def get_macro_context() -> Optional[ParseContext]:
    """Get the current macro context for this thread."""
    return getattr(_thread_local, "context", None)


def clear_macro_context() -> None:
    """Clear the current macro context for this thread."""
    if hasattr(_thread_local, "context"):
        delattr(_thread_local, "context")
