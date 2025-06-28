"""
Custom exceptions for FinnBil Analyzer.
"""


class FinnBilError(Exception):
    """Base exception for FinnBil application."""
    pass


class ConfigurationError(FinnBilError):
    """Raised when there's a configuration error."""
    pass


class DataFetchError(FinnBilError):
    """Raised when data fetching fails."""
    pass


class DataParsingError(FinnBilError):
    """Raised when data parsing fails."""
    pass


class AIServiceError(FinnBilError):
    """Raised when AI service encounters an error."""
    pass


class ValidationError(FinnBilError):
    """Raised when validation fails."""
    pass


class NetworkError(FinnBilError):
    """Raised when network operations fail."""
    pass
