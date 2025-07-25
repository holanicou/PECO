# -*- coding: utf-8 -*-
"""
Unit tests for LaTeX character escaping system.
Tests various input scenarios to ensure proper character handling.
"""

import unittest
from services.latex_processor import LaTeXProcessor
from services.exceptions import LaTeXError


class TestLaTeXProcessor(unittest.TestCase):
    """Test cases for LaTeXProcessor character escaping functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.processor = LaTeXProcessor()
    
    def test_basic_character_escaping(self):
        """Test escaping of basic problematic characters."""
        test_cases = [
            ('$', r'\$'),
            ('%', r'\%'),
            ('&', r'\&'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('^', r'\textasciicircum{}'),
            ('~', r'\textasciitilde{}'),
            ('\\', r'\textbackslash{}'),
            ('*', r'\textasteriskcentered{}'),
            ('[', r'{[}'),
            (']', r'{]}'),
            ('|', r'\textbar{}'),
            ('<', r'\textless{}'),
            ('>', r'\textgreater{}')
        ]
        
        for input_char, expected in test_cases:
            with self.subTest(char=input_char):
                result = self.processor.escape_special_characters(input_char)
                self.assertEqual(result, expected, 
                    f"Failed to escape '{input_char}' correctly")
    
    def test_currency_amounts(self):
        """Test escaping of currency amounts with dollar signs."""
        test_cases = [
            ('$100', r'\$100'),
            ('$1,234', r'\$1,234'),
            ('$1,234.56', r'\$1,234.56'),
            ('Gasto de $500 en comida', 'Gasto de \\$500 en comida'),
            ('Total: $1,500.75', 'Total: \\$1,500.75'),
            ('$0.99', r'\$0.99'),
            ('$999,999.99', r'\$999,999.99')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_special_characters(input_text)
                self.assertEqual(result, expected,
                    f"Failed to escape currency in '{input_text}'")
    
    def test_complex_text_with_multiple_characters(self):
        """Test escaping of complex text with multiple special characters."""
        test_cases = [
            (
                'Gasto de $100 en R&D (50% del presupuesto)',
                'Gasto de \\$100 en R\\&D (50\\% del presupuesto)'
            ),
            (
                'Inversión: $1,500 @ 5% anual',
                'Inversión: \\$1,500 @ 5\\% anual'
            ),
            (
                'Categoría: {Alimentación} - $250.50',
                'Categoría: \\{Alimentación\\} - \\$250.50'
            ),
            (
                'Nota: 100% efectivo & transferencia',
                'Nota: 100\\% efectivo \\& transferencia'
            ),
            (
                'Código: #ABC123_DEF',
                'Código: \\#ABC123\\_DEF'
            )
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_special_characters(input_text)
                self.assertEqual(result, expected,
                    f"Failed to escape complex text: '{input_text}'")
    
    def test_specialized_currency_escaping(self):
        """Test the specialized currency escaping method."""
        test_cases = [
            ('$100', r'\$100'),
            ('$1,234.56', r'\$1,234.56'),
            ('Compra por $500', 'Compra por \\$500'),
            ('$0.99 y $1,000', '\\$0.99 y \\$1,000'),
            ('No currency here', 'No currency here'),
            ('$', '$')  # Single $ without number should not be processed by currency method
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_currency_amounts(input_text)
                self.assertEqual(result, expected,
                    f"Currency escaping failed for: '{input_text}'")
    
    def test_description_processing(self):
        """Test the complete description processing workflow."""
        test_cases = [
            (
                'Compra de materiales por $1,500 (IVA incluido)',
                'Compra de materiales por \\$1,500 (IVA incluido)'
            ),
            (
                'Pago de servicios: $250.75 & $100.25',
                'Pago de servicios: \\$250.75 \\& \\$100.25'
            ),
            (
                'Inversión en acciones: $5,000 @ 3.5%',
                'Inversión en acciones: \\$5,000 @ 3.5\\%'
            ),
            (
                'Categoría {Transporte} - Uber: $45.50',
                'Categoría \\{Transporte\\} - Uber: \\$45.50'
            )
        ]
        
        for input_desc, expected in test_cases:
            with self.subTest(description=input_desc):
                result = self.processor.process_description(input_desc)
                self.assertEqual(result, expected,
                    f"Description processing failed for: '{input_desc}'")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty string
        self.assertEqual(self.processor.escape_special_characters(''), '')
        
        # None input should raise error
        with self.assertRaises(LaTeXError):
            self.processor.escape_special_characters(None)
        
        # Non-string input should raise error
        with self.assertRaises(LaTeXError):
            self.processor.escape_special_characters(123)
        
        # Very long string
        long_text = 'A' * 1000 + '$' + 'B' * 1000
        result = self.processor.escape_special_characters(long_text)
        self.assertIn(r'\$', result)
        self.assertEqual(len(result), len(long_text) + 1)  # One extra char for escape
        
        # String with only safe characters
        safe_text = 'This is completely safe text with numbers 123'
        result = self.processor.escape_special_characters(safe_text)
        self.assertEqual(result, safe_text)
    
    def test_backslash_handling(self):
        """Test proper handling of backslashes to avoid double-escaping."""
        test_cases = [
            ('\\', r'\textbackslash{}'),
            ('\\$', r'\textbackslash{}\$'),
            ('C:\\Users\\file', r'C:\textbackslash{}Users\textbackslash{}file'),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_special_characters(input_text)
                self.assertEqual(result, expected,
                    f"Backslash handling failed for: '{input_text}'")
    
    def test_validation_method(self):
        """Test the text validation functionality."""
        # Properly escaped text should validate
        escaped_text = r'This is \$ properly \% escaped \& text'
        self.assertTrue(self.processor.validate_escaped_text(escaped_text))
        
        # Unescaped text should not validate
        unescaped_text = 'This has $ unescaped % characters & more'
        self.assertFalse(self.processor.validate_escaped_text(unescaped_text))
        
        # Empty string should validate
        self.assertTrue(self.processor.validate_escaped_text(''))
        
        # Safe text should validate
        safe_text = 'This is completely safe text'
        self.assertTrue(self.processor.validate_escaped_text(safe_text))
    
    def test_mathematical_expressions(self):
        """Test handling of mathematical expressions and formulas."""
        test_cases = [
            ('x^2 + y^2 = z^2', r'x\textasciicircum{}2 + y\textasciicircum{}2 = z\textasciicircum{}2'),
            ('Rate: 5% ~ 6%', r'Rate: 5\% \textasciitilde{} 6\%'),
            ('Formula: {a + b} * c', r'Formula: \{a + b\} \textasteriskcentered{} c'),
            ('Range: [0, 100]', r'Range: {[}0, 100{]}')
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(text=input_text):
                result = self.processor.escape_special_characters(input_text)
                self.assertEqual(result, expected,
                    f"Mathematical expression escaping failed for: '{input_text}'")
    
    def test_real_world_scenarios(self):
        """Test real-world expense and investment descriptions."""
        test_cases = [
            (
                'Compra en supermercado: $125.50 (descuento 10%)',
                'Compra en supermercado: \\$125.50 (descuento 10\\%)'
            ),
            (
                'Transferencia bancaria: $2,500 - Comisión: $15',
                'Transferencia bancaria: \\$2,500 - Comisión: \\$15'
            ),
            (
                'Inversión ETF: $1,000 @ tasa variable ~3.5%',
                'Inversión ETF: \\$1,000 @ tasa variable \\textasciitilde{}3.5\\%'
            ),
            (
                'Pago servicios {Luz & Gas}: $180.75',
                'Pago servicios \\{Luz \\& Gas\\}: \\$180.75'
            ),
            (
                'Código de referencia: #PAY_2025_001',
                'Código de referencia: \\#PAY\\_2025\\_001'
            )
        ]
        
        for input_desc, expected in test_cases:
            with self.subTest(description=input_desc):
                result = self.processor.process_description(input_desc)
                self.assertEqual(result, expected,
                    f"Real-world scenario failed for: '{input_desc}'")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)