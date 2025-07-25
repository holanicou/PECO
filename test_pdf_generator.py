# -*- coding: utf-8 -*-
"""
Unit tests for PDFGenerator class.
Tests PDF generation capabilities, LaTeX compilation, and error handling.
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

from services.pdf_generator import PDFGenerator, PDFResult, CompilationResult
from services.latex_processor import LaTeXProcessor
from services.exceptions import LaTeXError, ConfigurationError


class TestPDFGenerator(unittest.TestCase):
    """Test cases for PDFGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.latex_processor = LaTeXProcessor()
        self.pdf_generator = PDFGenerator(self.latex_processor)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_check_latex_availability_success(self, mock_run):
        """Test successful LaTeX availability check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="pdfTeX 3.14159")
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ['pdflatex', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_check_latex_availability_not_found(self, mock_run):
        """Test LaTeX availability check when pdflatex is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_check_latex_availability_failure(self, mock_run):
        """Test LaTeX availability check when pdflatex returns error."""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertFalse(result)
    
    def test_process_template_data_strings(self):
        """Test template data processing with string values."""
        data = {
            'title': 'Test with $ special chars',
            'amount': '$1,234.56',
            'description': 'Payment & fees'
        }
        
        result = self.pdf_generator._process_template_data(data)
        
        self.assertEqual(result['title'], 'Test with \\$ special chars')
        self.assertEqual(result['amount'], '\\$1,234.56')
        self.assertEqual(result['description'], 'Payment \\& fees')
    
    def test_process_template_data_nested(self):
        """Test template data processing with nested structures."""
        data = {
            'expenses': [
                {'description': 'Food & drinks', 'amount': '$50.00'},
                {'description': 'Transport', 'amount': '$25.00'}
            ],
            'config': {
                'title': 'Monthly Report',
                'currency': '$'
            }
        }
        
        result = self.pdf_generator._process_template_data(data)
        
        self.assertEqual(result['expenses'][0]['description'], 'Food \\& drinks')
        self.assertEqual(result['expenses'][0]['amount'], '\\$50.00')
        self.assertEqual(result['config']['title'], 'Monthly Report')
        self.assertEqual(result['config']['currency'], '\\$')
    
    def test_process_template_file_not_found(self):
        """Test template processing with non-existent file."""
        non_existent_path = os.path.join(self.temp_dir, 'nonexistent.tex')
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template(non_existent_path, {})
        
        self.assertIn('Template file not found', str(context.exception))
    
    def test_process_template_directory_instead_of_file(self):
        """Test template processing when path points to directory."""
        # Create a directory instead of a file
        dir_path = os.path.join(self.temp_dir, 'template_dir')
        os.makedirs(dir_path)
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template(dir_path, {})
        
        self.assertIn('Template path is not a file', str(context.exception))
    
    def test_create_simple_template_and_process(self):
        """Test template processing with a simple template."""
        # Create a simple template
        template_content = """
\\documentclass{article}
\\begin{document}
Title: {{ title }}
Amount: {{ amount }}
\\end{document}
"""
        template_path = os.path.join(self.temp_dir, 'test_template.tex')
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        data = {'title': 'Test Document', 'amount': '$100.00'}
        
        result = self.pdf_generator.process_template(template_path, data)
        
        self.assertIn('Title: Test Document', result)
        self.assertIn('Amount: \\$100.00', result)
    
    @patch.object(PDFGenerator, 'check_latex_availability')
    def test_compile_to_pdf_latex_not_available(self, mock_check):
        """Test PDF compilation when LaTeX is not available."""
        mock_check.return_value = False
        
        tex_file = os.path.join(self.temp_dir, 'test.tex')
        with open(tex_file, 'w') as f:
            f.write('\\documentclass{article}\\begin{document}Test\\end{document}')
        
        with self.assertRaises(LaTeXError) as context:
            self.pdf_generator.compile_to_pdf(tex_file, self.temp_dir)
        
        self.assertIn('pdflatex is not available', str(context.exception))
    
    def test_compile_to_pdf_file_not_found(self):
        """Test PDF compilation with non-existent tex file."""
        non_existent_tex = os.path.join(self.temp_dir, 'nonexistent.tex')
        
        with patch.object(self.pdf_generator, 'check_latex_availability', return_value=True):
            with self.assertRaises(LaTeXError) as context:
                self.pdf_generator.compile_to_pdf(non_existent_tex, self.temp_dir)
        
        self.assertIn('LaTeX file not found', str(context.exception))
    
    def test_clean_temp_files(self):
        """Test cleaning of temporary files."""
        base_path = os.path.join(self.temp_dir, 'test')
        
        # Create some temporary files
        temp_files = ['.aux', '.log', '.fls']
        for ext in temp_files:
            temp_file = base_path + ext
            with open(temp_file, 'w') as f:
                f.write('temp content')
        
        # Clean the files
        self.pdf_generator.clean_temp_files(base_path)
        
        # Verify files are removed
        for ext in temp_files:
            temp_file = base_path + ext
            self.assertFalse(os.path.exists(temp_file))
    
    def test_clean_temp_files_custom_extensions(self):
        """Test cleaning of temporary files with custom extensions."""
        base_path = os.path.join(self.temp_dir, 'test')
        
        # Create files with custom extensions
        custom_extensions = ['.custom1', '.custom2']
        for ext in custom_extensions:
            temp_file = base_path + ext
            with open(temp_file, 'w') as f:
                f.write('temp content')
        
        # Clean with custom extensions
        result = self.pdf_generator.clean_temp_files(base_path, custom_extensions)
        
        # Verify files are removed
        for ext in custom_extensions:
            temp_file = base_path + ext
            self.assertFalse(os.path.exists(temp_file))
        
        # Verify cleanup result
        self.assertEqual(result['total_cleaned'], 2)
        self.assertEqual(result['total_failed'], 0)
    
    def test_clean_temp_files_returns_detailed_result(self):
        """Test that clean_temp_files returns detailed cleanup results."""
        base_path = os.path.join(self.temp_dir, 'test')
        
        # Create some temporary files
        temp_files = ['.aux', '.log']
        for ext in temp_files:
            temp_file = base_path + ext
            with open(temp_file, 'w') as f:
                f.write('temp content')
        
        # Clean the files
        result = self.pdf_generator.clean_temp_files(base_path, temp_files)
        
        # Verify result structure
        self.assertIn('cleaned_files', result)
        self.assertIn('failed_files', result)
        self.assertIn('permission_errors', result)
        self.assertIn('total_cleaned', result)
        self.assertIn('total_failed', result)
        
        # Verify counts
        self.assertEqual(result['total_cleaned'], 2)
        self.assertEqual(len(result['cleaned_files']), 2)
    
    def test_ensure_directory_structure_creates_directory(self):
        """Test directory structure creation."""
        new_dir = os.path.join(self.temp_dir, 'new_output_dir')
        
        # Ensure directory doesn't exist initially
        self.assertFalse(os.path.exists(new_dir))
        
        # Create directory structure
        result = self.pdf_generator.ensure_directory_structure(new_dir)
        
        # Verify directory was created
        self.assertTrue(result)
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
    
    def test_ensure_directory_structure_validates_existing_directory(self):
        """Test directory structure validation for existing directory."""
        existing_dir = os.path.join(self.temp_dir, 'existing_dir')
        os.makedirs(existing_dir)
        
        # Validate existing directory
        result = self.pdf_generator.ensure_directory_structure(existing_dir)
        
        self.assertTrue(result)
    
    def test_ensure_directory_structure_fails_for_file(self):
        """Test directory structure validation fails when path is a file."""
        file_path = os.path.join(self.temp_dir, 'not_a_directory.txt')
        with open(file_path, 'w') as f:
            f.write('test content')
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.ensure_directory_structure(file_path)
        
        self.assertIn('not a directory', str(context.exception))
    
    def test_validate_file_permissions_existing_file(self):
        """Test file permission validation for existing file."""
        test_file = os.path.join(self.temp_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # Test read permission
        result = self.pdf_generator.validate_file_permissions(test_file, 'r')
        self.assertTrue(result)
        
        # Test read/write permissions
        result = self.pdf_generator.validate_file_permissions(test_file, 'rw')
        self.assertTrue(result)
    
    def test_validate_file_permissions_nonexistent_file(self):
        """Test file permission validation for non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        
        result = self.pdf_generator.validate_file_permissions(nonexistent_file, 'r')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()