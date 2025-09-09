from pathlib import Path
from typing import Optional, Dict, Any


class ParseContext:
    """Context object that carries compilation state through the parser.

    This replaces global state and makes the parser reentrant.
    """

    def __init__(self, source_path: Optional[str] = None, source_code: str = ""):
        self.source_path = source_path
        self.source_code = source_code
        self.constants: Dict[str, Any] = {}

        # Base directory for resolving relative paths in macros
        if source_path:
            self.base_dir = Path(source_path).parent
        else:
            self.base_dir = Path.cwd()

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path from the current source file's directory."""
        return self.base_dir / relative_path
