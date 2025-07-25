# -*- coding: utf-8 -*-
"""
Services module for PECO financial application.
Contains core service classes, error handling, and data models.
"""

from .base import Result, PDFResult, AnalysisResult
from .exceptions import PECOError, LaTeXError, DataError, ConfigurationError
from .logging_config import setup_logging, get_logger
from .latex_processor import LaTeXProcessor
from .data_manager import DataManager
from .system_checker import SystemChecker, DependencyResult, ConfigurationResult

__all__ = [
    'Result',
    'PDFResult', 
    'AnalysisResult',
    'PECOError',
    'LaTeXError',
    'DataError',
    'ConfigurationError',
    'setup_logging',
    'get_logger',
    'LaTeXProcessor',
    'DataManager',
    'SystemChecker',
    'DependencyResult',
    'ConfigurationResult'
]