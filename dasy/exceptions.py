"""
Custom exception hierarchy for the Dasy compiler.

This module defines specific exception types for different error scenarios
in the Dasy compilation process, improving error handling and debugging.
"""


class DasyException(Exception):
    """Base exception for all Dasy-specific errors."""
    pass


class DasySyntaxError(DasyException):
    """Raised when Dasy source code has invalid syntax.
    
    Examples:
    - Invalid function declarations
    - Malformed expressions
    - Invalid tuple/array declarations
    """
    pass


class DasyParseError(DasyException):
    """Raised when parsing fails for structural reasons.
    
    Examples:
    - Unrecognized top-level forms
    - Structural parsing failures
    """
    pass


class DasyTypeError(DasyException):
    """Raised for type annotation and type-related errors.
    
    Examples:
    - Missing type annotations
    - Invalid type annotations
    - Type declaration errors
    """
    pass


class DasyCompilationError(DasyException):
    """Raised during the compilation process.
    
    General compilation errors that don't fit other categories.
    """
    pass


class DasyCircularDependencyError(DasyCompilationError):
    """Raised when circular dependencies are detected.
    
    This typically occurs with recursive includes or interfaces.
    """
    def __init__(self, message, path=None, stack=None):
        super().__init__(message)
        self.path = path
        self.stack = stack


class DasyNotImplementedError(DasyException):
    """Raised when using features not yet implemented.
    
    Examples:
    - Floating point support
    - Features planned for future releases
    """
    pass


class DasyUnsupportedError(DasyException):
    """Raised when using permanently unsupported features.
    
    Examples:
    - Node types that Dasy doesn't support
    - Features incompatible with the design
    """
    pass


class DasyUsageError(DasyException):
    """Raised for incorrect CLI usage or invalid user input.
    
    Examples:
    - Invalid output format specification
    - Incorrect command-line arguments
    """
    pass