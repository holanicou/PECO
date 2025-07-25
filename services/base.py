# -*- coding: utf-8 -*-
"""
Base data classes for consistent return types across the PECO application.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict, List


@dataclass
class Result:
    """Base result class for consistent return types across services."""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None

    def __bool__(self) -> bool:
        """Allow Result to be used in boolean contexts."""
        return self.success


@dataclass
class PDFResult(Result):
    """Result class specifically for PDF generation operations."""
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    compilation_log: Optional[str] = None


@dataclass
class AnalysisResult(Result):
    """Result class for financial analysis operations."""
    total_expenses: Optional[float] = None
    expenses_by_category: Optional[Dict[str, float]] = None
    total_investments: Optional[float] = None
    chart_path: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = None