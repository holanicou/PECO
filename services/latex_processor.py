# -*- coding: utf-8 -*-
"""
LaTeX processing utilities for the PECO application.
Handles character escaping and template processing for safe LaTeX compilation.
"""

import re
from typing import Dict, Optional
from .exceptions import LaTeXError
from .logging_config import get_logger

logger = get_logger(__name__)


class LaTeXProcessor:
    """
    Handles LaTeX text processing, character escaping, and template processing.
    
    This class provides safe processing of user input for LaTeX documents,
    ensuring that special characters are properly escaped to prevent compilation errors.
    """
    
    # Comprehensive mapping of problematic characters to their LaTeX-safe equivalents
    LATEX_ESCAPE_MAP = {
        '$': r'\$',
        '%': r'\%',
        '&': r'\&',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '^': r'\textasciicircum{}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
        '*': r'\textasteriskcentered{}',
        '[': r'{[}',
        ']': r'{]}',
        '|': r'\textbar{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}'
    }
    
    def __init__(self):
        """Initialize the LaTeX processor."""
        logger.debug("LaTeX processor initialized")
    
    def escape_special_characters(self, text: str) -> str:
        """
        Escape special characters in text to make it safe for LaTeX processing.
        
        This method handles all problematic characters that could cause LaTeX
        compilation errors, including currency symbols, mathematical operators,
        and markup characters.
        
        Args:
            text: Input text that may contain special characters
            
        Returns:
            Text with all special characters properly escaped for LaTeX
            
        Raises:
            LaTeXError: If text processing fails
        """
        if not isinstance(text, str):
            raise LaTeXError(
                f"Expected string input, got {type(text).__name__}",
                details={'input_type': type(text).__name__, 'input_value': str(text)}
            )
        
        if not text:
            return text
        
        try:
            logger.debug(f"Escaping special characters in text: {text[:50]}...")
            
            # Use a placeholder for backslash to avoid double-escaping
            BACKSLASH_PLACEHOLDER = "XBACKSLASHX"
            
            escaped_text = text
            
            # Replace backslashes with placeholder first
            if '\\' in escaped_text:
                escaped_text = escaped_text.replace('\\', BACKSLASH_PLACEHOLDER)
                logger.debug(f"Replaced '\\' with placeholder")
            
            # Process all other characters (excluding backslash)
            for char, replacement in self.LATEX_ESCAPE_MAP.items():
                if char != '\\' and char in escaped_text:
                    escaped_text = escaped_text.replace(char, replacement)
                    logger.debug(f"Replaced '{char}' with '{replacement}'")
            
            # Finally replace placeholder with proper backslash escape
            if BACKSLASH_PLACEHOLDER in escaped_text:
                escaped_text = escaped_text.replace(BACKSLASH_PLACEHOLDER, r'\textbackslash{}')
                logger.debug(f"Replaced placeholder with '\\textbackslash{{}}'")
            
            logger.debug(f"Character escaping completed. Result: {escaped_text[:50]}...")
            return escaped_text
            
        except Exception as e:
            logger.error(f"Failed to escape special characters: {e}")
            raise LaTeXError(
                f"Character escaping failed: {str(e)}",
                details={'original_text': text, 'error': str(e)}
            )
    
    def escape_currency_amounts(self, text: str) -> str:
        """
        Specialized method for escaping currency amounts with proper formatting.
        
        This method handles common currency patterns like "$1,234.56" and ensures
        they are properly formatted for LaTeX while maintaining readability.
        
        Args:
            text: Text containing currency amounts
            
        Returns:
            Text with currency amounts properly escaped
        """
        if not text:
            return text
        
        try:
            # Pattern to match currency amounts like $1,234.56 or $1234
            currency_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
            
            def replace_currency(match):
                amount = match.group(1)
                return f'\\${amount}'
            
            result = re.sub(currency_pattern, replace_currency, text)
            logger.debug(f"Currency escaping: '{text}' -> '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"Failed to escape currency amounts: {e}")
            raise LaTeXError(
                f"Currency escaping failed: {str(e)}",
                details={'original_text': text, 'error': str(e)}
            )
    
    def process_description(self, description: str) -> str:
        """
        Process expense/investment descriptions for safe LaTeX inclusion.
        
        This method uses general character escaping to ensure descriptions are LaTeX-safe.
        Currency amounts are handled as part of the general escaping process.
        
        Args:
            description: Raw description text from user input
            
        Returns:
            LaTeX-safe description text
        """
        if not description:
            return ""
        
        try:
            logger.debug(f"Processing description: {description}")
            
            # Use general character escaping which handles all special characters including $
            processed = self.escape_special_characters(description)
            
            logger.debug(f"Description processing completed: {processed}")
            return processed
            
        except Exception as e:
            logger.error(f"Failed to process description: {e}")
            raise LaTeXError(
                f"Description processing failed: {str(e)}",
                details={'original_description': description, 'error': str(e)}
            )
    
    def validate_escaped_text(self, text: str) -> bool:
        """
        Validate that text has been properly escaped for LaTeX.
        
        This method checks for common problematic patterns that might
        cause LaTeX compilation issues.
        
        Args:
            text: Text to validate
            
        Returns:
            True if text appears to be properly escaped, False otherwise
        """
        if not text:
            return True
        
        # Check for unescaped problematic characters
        problematic_patterns = [
            r'(?<!\\)\$(?!\$)',  # Unescaped single dollar signs
            r'(?<!\\)%',         # Unescaped percent signs
            r'(?<!\\)&',         # Unescaped ampersands
            r'(?<!\\)#',         # Unescaped hash symbols
            r'(?<!\\)_',         # Unescaped underscores
            r'(?<!\\)\{',        # Unescaped opening braces
            r'(?<!\\)\}',        # Unescaped closing braces
        ]
        
        for pattern in problematic_patterns:
            if re.search(pattern, text):
                logger.warning(f"Found potentially problematic pattern in text: {pattern}")
                return False
        
        return True