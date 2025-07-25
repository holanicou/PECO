# -*- coding: utf-8 -*-
"""
Unit tests for PDFGenerator service class.
Tests PDF generation, LaTeX compilation, template processing, and file management.
"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import os
import subprocess
from dataclasses import dataclass

from services.pdf_generator import PDFGenerator, PDFResult, CompilationResult
from services.latex_processor import LaTeXProcessor
from services.exceptions import LaTeXError, ConfigurationError


class TestPDFGenerator(unittest.TestCase):
    """Test cases for PDFGenerator service class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_latex_processor = Mock(spec=LaTeXProcessor)
        self.pdf_generator = PDFGenerator(latex_processor=self.mock_latex_processor)
    
    def test_init_with_latex_processor(self):
        """Test PDFGenerator initialization with provided LaTeX processor."""
        processor = Mock(spec=LaTeXProcessor)
        generator = PDFGenerator(latex_processor=processor)
        self.assertEqual(generator.latex_processor, processor)
    
    def test_init_without_latex_processor(self):
        """Test PDFGenerator initialization without LaTeX processor creates one."""
        generator = PDFGenerator()
        self.assertIsInstance(generator.latex_processor, LaTeXProcessor)
    
    @patch('services.pdf_generator.subprocess.run')
    def test_check_latex_availability_success(self, mock_run):
        """Test successful LaTeX availability check."""
        # Mock successful pdflatex version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "pdfTeX 3.14159265-2.6-1.40.21 (TeX Live 2020)"
        mock_run.return_value = mock_result
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ['pdflatex', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('services.pdf_generator.subprocess.run')
    def test_check_latex_availability_not_found(self, mock_run):
        """Test LaTeX availability check when pdflatex is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertFalse(result)
    
    @patch('services.pdf_generator.subprocess.run')
    def test_check_latex_availability_timeout(self, mock_run):
        """Test LaTeX availability check with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(['pdflatex', '--version'], 10)
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertFalse(result)
    
    @patch('services.pdf_generator.subprocess.run')
    def test_check_latex_availability_failure(self, mock_run):
        """Test LaTeX availability check with non-zero return code."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.pdf_generator.check_latex_availability()
        
        self.assertFalse(result)
    
    @patch('services.pdf_generator.PDFGenerator.check_latex_availability')
    def test_compile_to_pdf_latex_not_available(self, mock_check):
        """Test PDF compilation when LaTeX is not available."""
        mock_check.return_value = False
        
        with self.assertRaises(LaTeXError) as context:
            self.pdf_generator.compile_to_pdf("test.tex", "output")
        
        self.assertIn("pdflatex is not available", str(context.exception))
        self.assertIn("Install MiKTeX or TeX Live", context.exception.details['suggestion'])
    
    @patch('services.pdf_generator.PDFGenerator.check_latex_availability')
    @patch('services.pdf_generator.os.path.exists')
    def test_compile_to_pdf_tex_file_not_found(self, mock_exists, mock_check):
        """Test PDF compilation when tex file doesn't exist."""
        mock_check.return_value = True
        mock_exists.return_value = False
        
        with self.assertRaises(LaTeXError) as context:
            self.pdf_generator.compile_to_pdf("nonexistent.tex", "output")
        
        self.assertIn("LaTeX file not found", str(context.exception))
        self.assertEqual(context.exception.details['tex_file'], "nonexistent.tex")
    
    @patch('services.pdf_generator.PDFGenerator.check_latex_availability')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.subprocess.run')
    def test_compile_to_pdf_success(self, mock_run, mock_makedirs, mock_exists, mock_check):
        """Test successful PDF compilation."""
        # Setup mocks
        mock_check.return_value = True
        mock_exists.side_effect = lambda path: path == "test.tex" or path.endswith("test.pdf")
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "LaTeX compilation successful"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.pdf_generator.compile_to_pdf("test.tex", "output")
        
        self.assertTrue(result.success)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout, "LaTeX compilation successful")
        self.assertTrue(result.pdf_created)
        
        # Verify subprocess call
        mock_run.assert_called_once_with(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', 'output', 'test.tex'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60
        )
    
    @patch('services.pdf_generator.PDFGenerator.check_latex_availability')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.subprocess.run')
    def test_compile_to_pdf_with_warnings(self, mock_run, mock_makedirs, mock_exists, mock_check):
        """Test PDF compilation with warnings but successful PDF creation."""
        # Setup mocks
        mock_check.return_value = True
        mock_exists.side_effect = lambda path: path == "test.tex" or path.endswith("test.pdf")
        
        mock_result = Mock()
        mock_result.returncode = 1  # LaTeX warnings
        mock_result.stdout = "LaTeX Warning: Some warning message"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.pdf_generator.compile_to_pdf("test.tex", "output")
        
        # Should still be successful if PDF was created
        self.assertTrue(result.success)
        self.assertTrue(result.pdf_created)
        self.assertEqual(result.return_code, 1)
    
    @patch('services.pdf_generator.PDFGenerator.check_latex_availability')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.subprocess.run')
    def test_compile_to_pdf_failure(self, mock_run, mock_makedirs, mock_exists, mock_check):
        """Test PDF compilation failure."""
        # Setup mocks
        mock_check.return_value = True
        mock_exists.side_effect = lambda path: path == "test.tex"  # PDF not created
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "LaTeX Error: Something went wrong"
        mock_result.stderr = "Error details"
        mock_run.return_value = mock_result
        
        result = self.pdf_generator.compile_to_pdf("test.tex", "output")
        
        self.assertFalse(result.success)
        self.assertFalse(result.pdf_created)
        self.assertEqual(result.return_code, 1)
        self.assertIn("Something went wrong", result.stdout)
    
    @patch('services.pdf_generator.PDFGenerator.check_latex_availability')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.subprocess.run')
    def test_compile_to_pdf_timeout(self, mock_run, mock_makedirs, mock_exists, mock_check):
        """Test PDF compilation timeout."""
        mock_check.return_value = True
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired(['pdflatex'], 60)
        
        with self.assertRaises(LaTeXError) as context:
            self.pdf_generator.compile_to_pdf("test.tex", "output")
        
        self.assertIn("timed out after 60 seconds", str(context.exception))
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.access')
    @patch('services.pdf_generator.os.path.isfile')
    def test_process_template_file_not_found(self, mock_isfile, mock_access, mock_exists):
        """Test template processing when file doesn't exist."""
        mock_exists.return_value = False
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template("nonexistent.tex", {})
        
        self.assertIn("Template file not found", str(context.exception))
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.access')
    @patch('services.pdf_generator.os.path.isfile')
    def test_process_template_file_not_readable(self, mock_isfile, mock_access, mock_exists):
        """Test template processing when file is not readable."""
        mock_exists.return_value = True
        mock_access.return_value = False  # No read access
        mock_isfile.return_value = True
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template("template.tex", {})
        
        self.assertIn("not readable", str(context.exception))
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.access')
    @patch('services.pdf_generator.os.path.isfile')
    def test_process_template_not_a_file(self, mock_isfile, mock_access, mock_exists):
        """Test template processing when path is not a file."""
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_isfile.return_value = False  # Not a file (maybe directory)
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.process_template("template.tex", {})
        
        self.assertIn("not a file", str(context.exception))
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.access')
    @patch('services.pdf_generator.os.path.isfile')
    @patch('services.pdf_generator.Environment')
    def test_process_template_success(self, mock_env_class, mock_isfile, mock_access, mock_exists):
        """Test successful template processing."""
        # Setup mocks
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_isfile.return_value = True
        
        mock_template = Mock()
        mock_template.render.return_value = "Rendered template content"
        
        mock_env = Mock()
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env
        
        # Mock the data processing
        self.mock_latex_processor.escape_special_characters.side_effect = lambda x: f"escaped_{x}"
        
        data = {"title": "Test Title", "amount": "$100"}
        result = self.pdf_generator.process_template("/path/template.tex", data)
        
        self.assertEqual(result, "Rendered template content")
        mock_template.render.assert_called_once()
    
    def test_process_template_data_strings(self):
        """Test processing template data with strings."""
        self.mock_latex_processor.escape_special_characters.side_effect = lambda x: f"escaped_{x}"
        
        data = {"title": "Test Title", "description": "Test & Description"}
        result = self.pdf_generator._process_template_data(data)
        
        expected = {"title": "escaped_Test Title", "description": "escaped_Test & Description"}
        self.assertEqual(result, expected)
    
    def test_process_template_data_mixed_types(self):
        """Test processing template data with mixed types."""
        self.mock_latex_processor.escape_special_characters.side_effect = lambda x: f"escaped_{x}"
        
        data = {
            "title": "Test Title",
            "amount": 100.50,
            "active": True,
            "items": ["item1", "item2"],
            "config": {"key": "value"}
        }
        result = self.pdf_generator._process_template_data(data)
        
        expected = {
            "title": "escaped_Test Title",
            "amount": 100.50,
            "active": True,
            "items": ["escaped_item1", "escaped_item2"],
            "config": {"key": "escaped_value"}
        }
        self.assertEqual(result, expected)
    
    def test_process_list_data(self):
        """Test processing list data."""
        self.mock_latex_processor.escape_special_characters.side_effect = lambda x: f"escaped_{x}"
        
        data_list = ["string1", 123, {"key": "value"}, ["nested", "list"]]
        result = self.pdf_generator._process_list_data(data_list)
        
        expected = ["escaped_string1", 123, {"key": "escaped_value"}, ["escaped_nested", "escaped_list"]]
        self.assertEqual(result, expected)
    
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.path.isdir')
    @patch('services.pdf_generator.os.access')
    def test_ensure_directory_structure_success(self, mock_access, mock_isdir, mock_exists, mock_makedirs):
        """Test successful directory structure validation."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        
        result = self.pdf_generator.ensure_directory_structure("test_dir")
        
        self.assertTrue(result)
        mock_makedirs.assert_not_called()  # Directory already exists
    
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.path.isdir')
    @patch('services.pdf_generator.os.access')
    def test_ensure_directory_structure_creates_directory(self, mock_access, mock_isdir, mock_exists, mock_makedirs):
        """Test directory creation when it doesn't exist."""
        mock_exists.side_effect = [False, True]  # Doesn't exist, then exists after creation
        mock_isdir.return_value = True
        mock_access.return_value = True
        
        result = self.pdf_generator.ensure_directory_structure("test_dir")
        
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)
    
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.path.isdir')
    def test_ensure_directory_structure_not_directory(self, mock_isdir, mock_exists, mock_makedirs):
        """Test directory validation when path exists but is not a directory."""
        mock_exists.return_value = True
        mock_isdir.return_value = False  # Exists but not a directory
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.ensure_directory_structure("test_dir")
        
        self.assertIn("not a directory", str(context.exception))
    
    @patch('services.pdf_generator.os.makedirs')
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.path.isdir')
    @patch('services.pdf_generator.os.access')
    def test_ensure_directory_structure_no_write_permission(self, mock_access, mock_isdir, mock_exists, mock_makedirs):
        """Test directory validation with no write permission."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.side_effect = lambda path, mode: mode != os.W_OK  # No write access
        
        with self.assertRaises(ConfigurationError) as context:
            self.pdf_generator.ensure_directory_structure("test_dir")
        
        self.assertIn("No write permission", str(context.exception))
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.remove')
    @patch('services.pdf_generator.os.access')
    def test_clean_temp_files_success(self, mock_access, mock_remove, mock_exists):
        """Test successful temporary file cleanup."""
        mock_exists.side_effect = lambda path: path.endswith(('.aux', '.log'))
        mock_access.return_value = True  # Has write permission
        
        result = self.pdf_generator.clean_temp_files("test_file")
        
        self.assertEqual(result['total_cleaned'], 2)
        self.assertIn('test_file.aux', result['cleaned_files'])
        self.assertIn('test_file.log', result['cleaned_files'])
        self.assertEqual(result['total_failed'], 0)
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.remove')
    @patch('services.pdf_generator.os.access')
    def test_clean_temp_files_permission_error(self, mock_access, mock_remove, mock_exists):
        """Test temporary file cleanup with permission errors."""
        mock_exists.return_value = True
        mock_access.return_value = False  # No write permission
        
        result = self.pdf_generator.clean_temp_files("test_file", ['.aux'])
        
        self.assertEqual(result['total_cleaned'], 0)
        self.assertEqual(result['total_failed'], 1)
        self.assertIn('test_file.aux', result['permission_errors'])
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.remove')
    @patch('services.pdf_generator.os.access')
    def test_clean_temp_files_removal_error(self, mock_access, mock_remove, mock_exists):
        """Test temporary file cleanup with removal errors."""
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_remove.side_effect = OSError("Permission denied")
        
        result = self.pdf_generator.clean_temp_files("test_file", ['.aux'])
        
        self.assertEqual(result['total_cleaned'], 0)
        self.assertEqual(result['total_failed'], 1)
        self.assertEqual(len(result['failed_files']), 1)
        self.assertEqual(result['failed_files'][0][0], 'test_file.aux')
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.shutil.copy2')
    def test_copy_template_resources_success(self, mock_copy, mock_exists):
        """Test successful template resource copying."""
        mock_exists.side_effect = lambda path: 'logo.png' in path or 'firma.png' in path
        
        result = self.pdf_generator._copy_template_resources("/path/template.tex", "output")
        
        self.assertEqual(result['total_copied'], 2)
        self.assertIn('logo.png', result['copied_files'])
        self.assertIn('firma.png', result['copied_files'])
        self.assertEqual(result['total_failed'], 0)
    
    @patch('services.pdf_generator.os.path.exists')
    def test_copy_template_resources_missing_files(self, mock_exists):
        """Test template resource copying with missing files."""
        mock_exists.return_value = False  # No resource files exist
        
        result = self.pdf_generator._copy_template_resources("/path/template.tex", "output")
        
        self.assertEqual(result['total_copied'], 0)
        self.assertEqual(result['total_missing'], 2)
        self.assertIn('logo.png', result['missing_files'])
        self.assertIn('firma.png', result['missing_files'])
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.access')
    def test_validate_file_permissions_success(self, mock_access, mock_exists):
        """Test successful file permission validation."""
        mock_exists.return_value = True
        mock_access.return_value = True
        
        result = self.pdf_generator.validate_file_permissions("test.txt", "rw")
        
        self.assertTrue(result)
    
    @patch('services.pdf_generator.os.path.exists')
    def test_validate_file_permissions_file_not_found(self, mock_exists):
        """Test file permission validation when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.pdf_generator.validate_file_permissions("test.txt", "rw")
        
        self.assertFalse(result)
    
    @patch('services.pdf_generator.os.path.exists')
    @patch('services.pdf_generator.os.access')
    def test_validate_file_permissions_no_read_access(self, mock_access, mock_exists):
        """Test file permission validation with no read access."""
        mock_exists.return_value = True
        mock_access.side_effect = lambda path, mode: mode != os.R_OK
        
        result = self.pdf_generator.validate_file_permissions("test.txt", "r")
        
        self.assertFalse(result)
    
    @patch('services.pdf_generator.PDFGenerator.ensure_directory_structure')
    @patch('services.pdf_generator.PDFGenerator.process_template')
    @patch('services.pdf_generator.PDFGenerator._copy_template_resources')
    @patch('services.pdf_generator.PDFGenerator.compile_to_pdf')
    @patch('services.pdf_generator.PDFGenerator.clean_temp_files')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_resolution_success(self, mock_file, mock_clean, mock_compile, mock_copy, mock_template, mock_ensure):
        """Test successful resolution generation."""
        # Setup mocks
        mock_ensure.return_value = True
        mock_template.return_value = "LaTeX content"
        mock_copy.return_value = {"total_copied": 2}
        
        mock_compilation = CompilationResult(
            success=True,
            stdout="Compilation successful",
            stderr="",
            return_code=0,
            pdf_created=True
        )
        mock_compile.return_value = mock_compilation
        mock_clean.return_value = {"total_cleaned": 2}
        
        result = self.pdf_generator.generate_resolution(
            "template.tex", {"title": "Test"}, "output", "test_resolution"
        )
        
        self.assertTrue(result.success)
        self.assertIn("test_resolution.pdf", result.pdf_path)
        self.assertIn("test_resolution.tex", result.tex_path)
        self.assertEqual(result.compilation_log, "Compilation successful")
    
    @patch('services.pdf_generator.PDFGenerator.ensure_directory_structure')
    def test_generate_resolution_directory_error(self, mock_ensure):
        """Test resolution generation with directory error."""
        mock_ensure.side_effect = ConfigurationError("Directory error", {})
        
        result = self.pdf_generator.generate_resolution(
            "template.tex", {"title": "Test"}, "output", "test_resolution"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DIRECTORY_ERROR")
        self.assertIn("Directory validation failed", result.message)
    
    @patch('services.pdf_generator.PDFGenerator.ensure_directory_structure')
    @patch('services.pdf_generator.PDFGenerator.process_template')
    def test_generate_resolution_template_error(self, mock_template, mock_ensure):
        """Test resolution generation with template processing error."""
        mock_ensure.return_value = True
        mock_template.side_effect = Exception("Template error")
        
        result = self.pdf_generator.generate_resolution(
            "template.tex", {"title": "Test"}, "output", "test_resolution"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "TEMPLATE_ERROR")
        self.assertIn("Template processing failed", result.message)
    
    @patch('services.pdf_generator.PDFGenerator.ensure_directory_structure')
    @patch('services.pdf_generator.PDFGenerator.process_template')
    @patch('services.pdf_generator.PDFGenerator._copy_template_resources')
    @patch('services.pdf_generator.PDFGenerator.compile_to_pdf')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_resolution_compilation_failure(self, mock_file, mock_compile, mock_copy, mock_template, mock_ensure):
        """Test resolution generation with compilation failure."""
        # Setup mocks
        mock_ensure.return_value = True
        mock_template.return_value = "LaTeX content"
        mock_copy.return_value = {"total_copied": 2}
        
        mock_compilation = CompilationResult(
            success=False,
            stdout="Compilation failed",
            stderr="LaTeX Error: Undefined control sequence",
            return_code=1,
            pdf_created=False
        )
        mock_compile.return_value = mock_compilation
        
        result = self.pdf_generator.generate_resolution(
            "template.tex", {"title": "Test"}, "output", "test_resolution"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "COMPILATION_FAILED")
        self.assertIn("PDF compilation failed", result.message)
        self.assertEqual(result.compilation_log, "Compilation failed")


if __name__ == '__main__':
    unittest.main()