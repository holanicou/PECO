# -*- coding: utf-8 -*-
"""
Unit tests for LaTeXProcessor service class.
Tests character escaping, currency handling, and text processing functionality.
"""

import unittest
from unittest.mock import patch

from services.latex_processor import LaTeXProcessor
from services.exceptions import LaTeXError


class TestLaTeXProcessor(unittest.TestCase):
    """Test cases for LaTeXProcessor service class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = LaTeXProcessor()
    
    def test_init(self):
        """Test LaTeXProcessor initialization."""
        processor = LaTeXProcessor()
        self.assertIsInstance(processor, LaTeXProcessor)
        self.assertIsInstance(processor.LATEX_ESCAPE_MAP, dict)
    
    def test_escape_special_characters_empty_string(self):
        """Test escaping empty string."""
        result = self.processor.escape_special_characters("")
        self.assertEqual(result, "")
    
    def test_escape_special_characters_no_special_chars(self):
        """Test escaping string with no special characters."""
        text = "This is a normal string with no special characters"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, text)
    
    def test_escape_special_characters_dollar_sign(self):
        """Test escaping dollar sign."""
        text = "This costs $50"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "This costs \\$50")
    
    def test_escape_special_characters_multiple_dollars(self):
        """Test escaping multiple dollar signs."""
        text = "Price: $100, Tax: $15, Total: $115"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Price: \\$100, Tax: \\$15, Total: \\$115")
    
    def test_escape_special_characters_percent(self):
        """Test escaping percent sign."""
        text = "Discount: 15%"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Discount: 15\\%")
    
    def test_escape_special_characters_ampersand(self):
        """Test escaping ampersand."""
        text = "Johnson & Johnson"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Johnson \\& Johnson")
    
    def test_escape_special_characters_hash(self):
        """Test escaping hash symbol."""
        text = "Reference #12345"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Reference \\#12345")
    
    def test_escape_special_characters_underscore(self):
        """Test escaping underscore."""
        text = "file_name.txt"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "file\\_name.txt")
    
    def test_escape_special_characters_braces(self):
        """Test escaping curly braces."""
        text = "Object {key: value}"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Object \\{key: value\\}")
    
    def test_escape_special_characters_caret(self):
        """Test escaping caret symbol."""
        text = "Power: 2^3"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Power: 2\\textasciicircum{}3")
    
    def test_escape_special_characters_tilde(self):
        """Test escaping tilde."""
        text = "Path: ~/documents"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Path: \\textasciitilde{}/documents")
    
    def test_escape_special_characters_backslash(self):
        """Test escaping backslash."""
        text = "Path: C:\\Users\\John"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Path: C:\\textbackslash{}Users\\textbackslash{}John")
    
    def test_escape_special_characters_asterisk(self):
        """Test escaping asterisk."""
        text = "Note: *important*"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Note: \\textasteriskcentered{}important\\textasteriskcentered{}")
    
    def test_escape_special_characters_brackets(self):
        """Test escaping square brackets."""
        text = "Array[0]"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Array{[}0{]}")
    
    def test_escape_special_characters_pipe(self):
        """Test escaping pipe symbol."""
        text = "Command | grep"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "Command \\textbar{} grep")
    
    def test_escape_special_characters_angle_brackets(self):
        """Test escaping angle brackets."""
        text = "HTML: <div>content</div>"
        result = self.processor.escape_special_characters(text)
        self.assertEqual(result, "HTML: \\textless{}div\\textgreater{}content\\textless{}/div\\textgreater{}")
    
    def test_escape_special_characters_comprehensive(self):
        """Test escaping multiple special characters in one string."""
        text = "Cost: $100 (15% tax) & handling fee #123 for file_name.txt"
        result = self.processor.escape_special_characters(text)
        expected = "Cost: \\$100 (15\\% tax) \\& handling fee \\#123 for file\\_name.txt"
        self.assertEqual(result, expected)
    
    def test_escape_special_characters_complex_currency(self):
        """Test escaping complex currency expressions."""
        text = "Total: $1,234.56 + $789.00 = $2,023.56"
        result = self.processor.escape_special_characters(text)
        expected = "Total: \\$1,234.56 + \\$789.00 = \\$2,023.56"
        self.assertEqual(result, expected)
    
    def test_escape_special_characters_invalid_input_type(self):
        """Test escaping with invalid input type."""
        with self.assertRaises(LaTeXError) as context:
            self.processor.escape_special_characters(123)
        
        self.assertIn("Expected string input", str(context.exception))
        self.assertEqual(context.exception.details['input_type'], 'int')
    
    def test_escape_special_characters_none_input(self):
        """Test escaping with None input."""
        with self.assertRaises(LaTeXError) as context:
            self.processor.escape_special_characters(None)
        
        self.assertIn("Expected string input", str(context.exception))
        self.assertEqual(context.exception.details['input_type'], 'NoneType')
    
    def test_escape_currency_amounts_simple(self):
        """Test escaping simple currency amounts."""
        text = "Price is $123.45"
        result = self.processor.escape_currency_amounts(text)
        self.assertEqual(result, "Price is \\$123.45")
    
    def test_escape_currency_amounts_with_commas(self):
        """Test escaping currency amounts with comma separators."""
        text = "Total: $1,234.56"
        result = self.processor.escape_currency_amounts(text)
        self.assertEqual(result, "Total: \\$1,234.56")
    
    def test_escape_currency_amounts_no_decimals(self):
        """Test escaping currency amounts without decimals."""
        text = "Cost: $1000"
        result = self.processor.escape_currency_amounts(text)
        self.assertEqual(result, "Cost: \\$1000")
    
    def test_escape_currency_amounts_multiple(self):
        """Test escaping multiple currency amounts."""
        text = "Item 1: $50.00, Item 2: $1,200.50, Total: $1,250.50"
        result = self.processor.escape_currency_amounts(text)
        expected = "Item 1: \\$50.00, Item 2: \\$1,200.50, Total: \\$1,250.50"
        self.assertEqual(result, expected)
    
    def test_escape_currency_amounts_empty_string(self):
        """Test escaping currency amounts with empty string."""
        result = self.processor.escape_currency_amounts("")
        self.assertEqual(result, "")
    
    def test_escape_currency_amounts_no_currency(self):
        """Test escaping text with no currency amounts."""
        text = "This text has no currency symbols"
        result = self.processor.escape_currency_amounts(text)
        self.assertEqual(result, text)
    
    def test_process_description_simple(self):
        """Test processing simple description."""
        description = "Lunch at restaurant"
        result = self.processor.process_description(description)
        self.assertEqual(result, "Lunch at restaurant")
    
    def test_process_description_with_currency(self):
        """Test processing description with currency."""
        description = "Lunch at restaurant - $25.50"
        result = self.processor.process_description(description)
        self.assertEqual(result, "Lunch at restaurant - \\$25.50")
    
    def test_process_description_with_special_chars(self):
        """Test processing description with various special characters."""
        description = "Johnson & Sons - 15% discount on item #123"
        result = self.processor.process_description(description)
        expected = "Johnson \\& Sons - 15\\% discount on item \\#123"
        self.assertEqual(result, expected)
    
    def test_process_description_empty(self):
        """Test processing empty description."""
        result = self.processor.process_description("")
        self.assertEqual(result, "")
    
    def test_process_description_none(self):
        """Test processing None description."""
        result = self.processor.process_description(None)
        self.assertEqual(result, "")
    
    def test_process_description_complex(self):
        """Test processing complex description with multiple special characters."""
        description = "Payment to Smith & Co. for services (invoice #456) - $1,250.75 + 10% tax"
        result = self.processor.process_description(description)
        expected = "Payment to Smith \\& Co. for services (invoice \\#456) - \\$1,250.75 + 10\\% tax"
        self.assertEqual(result, expected)
    
    def test_validate_escaped_text_valid(self):
        """Test validation of properly escaped text."""
        text = "This is \\$100 with \\% and \\& symbols"
        result = self.processor.validate_escaped_text(text)
        self.assertTrue(result)
    
    def test_validate_escaped_text_empty(self):
        """Test validation of empty text."""
        result = self.processor.validate_escaped_text("")
        self.assertTrue(result)
    
    def test_validate_escaped_text_unescaped_dollar(self):
        """Test validation of text with unescaped dollar sign."""
        text = "This costs $100"
        result = self.processor.validate_escaped_text(text)
        self.assertFalse(result)
    
    def test_validate_escaped_text_unescaped_percent(self):
        """Test validation of text with unescaped percent."""
        text = "Discount: 15%"
        result = self.processor.validate_escaped_text(text)
        self.assertFalse(result)
    
    def test_validate_escaped_text_unescaped_ampersand(self):
        """Test validation of text with unescaped ampersand."""
        text = "Johnson & Johnson"
        result = self.processor.validate_escaped_text(text)
        self.assertFalse(result)
    
    def test_validate_escaped_text_unescaped_hash(self):
        """Test validation of text with unescaped hash."""
        text = "Reference #123"
        result = self.processor.validate_escaped_text(text)
        self.assertFalse(result)
    
    def test_validate_escaped_text_unescaped_underscore(self):
        """Test validation of text with unescaped underscore."""
        text = "file_name.txt"
        result = self.processor.validate_escaped_text(text)
        self.assertFalse(result)
    
    def test_validate_escaped_text_unescaped_braces(self):
        """Test validation of text with unescaped braces."""
        text = "Object {key: value}"
        result = self.processor.validate_escaped_text(text)
        self.assertFalse(result)
    
    def test_validate_escaped_text_escaped_dollar_signs(self):
        """Test validation of text with properly escaped dollar signs."""
        text = "This costs \\$100 and \\$200"
        result = self.processor.validate_escaped_text(text)
        self.assertTrue(result)
    
    def test_validate_escaped_text_math_mode_dollars(self):
        """Test validation detects unescaped single dollars even in math context."""
        text = "Formula: $$x = y + z$$"
        result = self.processor.validate_escaped_text(text)
        # The current implementation detects single dollars even in double dollar context
        # This is actually correct behavior for safety
        self.assertFalse(result)
    
    @patch('services.latex_processor.logger')
    def test_escape_special_characters_logging(self, mock_logger):
        """Test that character escaping logs appropriately."""
        text = "Test $100"
        self.processor.escape_special_characters(text)
        
        # Verify debug logging was called
        mock_logger.debug.assert_called()
    
    def test_escape_special_characters_preserves_unicode(self):
        """Test that escaping preserves Unicode characters."""
        text = "Café costs $15.50 with 10% tip"
        result = self.processor.escape_special_characters(text)
        expected = "Café costs \\$15.50 with 10\\% tip"
        self.assertEqual(result, expected)
    
    def test_escape_special_characters_edge_cases(self):
        """Test escaping edge cases."""
        # Test string with only special characters
        text = "$%&#_{}^~\\"
        result = self.processor.escape_special_characters(text)
        expected = "\\$\\%\\&\\#\\_\\{\\}\\textasciicircum{}\\textasciitilde{}\\textbackslash{}"
        self.assertEqual(result, expected)
    
    def test_escape_special_characters_repeated_chars(self):
        """Test escaping repeated special characters."""
        text = "$$$ and %%% and &&&"
        result = self.processor.escape_special_characters(text)
        expected = "\\$\\$\\$ and \\%\\%\\% and \\&\\&\\&"
        self.assertEqual(result, expected)
    
    def test_escape_special_characters_mixed_with_normal_text(self):
        """Test escaping special characters mixed with normal text."""
        text = "Normal text with $pecial ch@racters & symbols 100%"
        result = self.processor.escape_special_characters(text)
        expected = "Normal text with \\$pecial ch@racters \\& symbols 100\\%"
        self.assertEqual(result, expected)
    
    def test_backslash_handling_order(self):
        """Test that backslashes are handled correctly to avoid double-escaping."""
        text = "Path: C:\\folder\\file.txt"
        result = self.processor.escape_special_characters(text)
        expected = "Path: C:\\textbackslash{}folder\\textbackslash{}file.txt"
        self.assertEqual(result, expected)
        
        # Verify no double-escaping occurred
        self.assertNotIn("\\\\", result)
        self.assertNotIn("textbackslashtextbackslash", result)


if __name__ == '__main__':
    unittest.main()