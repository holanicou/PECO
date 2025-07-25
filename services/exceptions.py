# -*- coding: utf-8 -*-
"""
Custom exception classes for the PECO application.
Provides centralized error management with specific error types.
"""

from typing import Optional, Dict, Any


class PECOError(Exception):
    """Base exception class for all PECO application errors."""
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize PECO error.
        
        Args:
            message: Human-readable error message
            error_code: Unique error code for programmatic handling
            details: Additional error details for debugging
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return formatted error message."""
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }


class LaTeXError(PECOError):
    """Exception for LaTeX processing and PDF generation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "LATEX_ERROR", details)


class DataError(PECOError):
    """Exception for data processing and validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATA_ERROR", details)


class ConfigurationError(PECOError):
    """Exception for configuration and system setup errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)