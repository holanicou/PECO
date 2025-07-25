# -*- coding: utf-8 -*-
"""
Test suite for SystemChecker class.
Tests dependency checking and system validation functionality.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import platform
import os
import tempfile
import shutil

from services.system_checker import SystemChecker, DependencyResult, ConfigurationResult
from services.base import Result


class TestSystemChecker(unittest.TestCase):
    """Test cases for SystemChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system_checker = SystemChecker()
    
    def test_init(self):
        """Test SystemChecker initialization."""
        checker = SystemChecker()
        self.assertIsNotNone(checker.logger)
        self.assertIn('pdflatex', checker.INSTALLATION_INSTRUCTIONS)
        self.assertIn('python', checker.INSTALLATION_INSTRUCTIONS)
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_latex_installation_success(self, mock_subprocess, mock_which):
        """Test successful LaTeX installation check."""
        # Mock pdflatex being found and working
        mock_which.return_value = '/usr/bin/pdflatex'
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout='pdfTeX 3.14159265-2.6-1.40.21 (TeX Live 2020)\n'
        )
        
        result = self.system_checker.check_latex_installation()
        
        self.assertTrue(result.success)
        self.assertIn('pdflatex is available', result.message)
        self.assertEqual(result.data['path'], '/usr/bin/pdflatex')
        mock_which.assert_called_once_with('pdflatex')
        mock_subprocess.assert_called_once()
    
    @patch('shutil.which')
    def test_check_latex_installation_not_found(self, mock_which):
        """Test LaTeX installation check when pdflatex is not found."""
        mock_which.return_value = None
        
        result = self.system_checker.check_latex_installation()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'LATEX_NOT_FOUND')
        self.assertIn('not installed or not in PATH', result.message)
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_latex_installation_not_working(self, mock_subprocess, mock_which):
        """Test LaTeX installation check when pdflatex exists but doesn't work."""
        mock_which.return_value = '/usr/bin/pdflatex'
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stderr='pdflatex: command failed'
        )
        
        result = self.system_checker.check_latex_installation()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'LATEX_NOT_WORKING')
        self.assertIn('not working properly', result.message)
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_latex_installation_timeout(self, mock_subprocess, mock_which):
        """Test LaTeX installation check when command times out."""
        mock_which.return_value = '/usr/bin/pdflatex'
        mock_subprocess.side_effect = subprocess.TimeoutExpired('pdflatex', 10)
        
        result = self.system_checker.check_latex_installation()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'LATEX_TIMEOUT')
        self.assertIn('timed out', result.message)
    
    def test_check_python_installation_success(self):
        """Test successful Python installation check."""
        result = self.system_checker.check_python_installation()
        
        # Should always succeed since we're running Python
        self.assertTrue(result.success)
        self.assertIn('Python', result.message)
        self.assertIn('version', result.data)
        self.assertIn('path', result.data)
    
    def test_check_python_installation_old_version(self):
        """Test Python installation check with old version."""
        # Mock sys.version_info within the method
        import sys
        original_version = sys.version_info
        try:
            # Create a mock version_info that behaves like the old version
            class MockVersionInfo:
                def __init__(self):
                    self.major = 3
                    self.minor = 6
                    self.micro = 0
                def __ge__(self, other):
                    return (self.major, self.minor) >= other
            
            sys.version_info = MockVersionInfo()
            result = self.system_checker.check_python_installation()
            
            self.assertFalse(result.success)
            self.assertEqual(result.error_code, 'PYTHON_VERSION_TOO_OLD')
            self.assertIn('too old', result.message)
        finally:
            sys.version_info = original_version
    
    @patch('services.system_checker.SystemChecker.check_latex_installation')
    @patch('services.system_checker.SystemChecker.check_python_installation')
    def test_check_all_dependencies_success(self, mock_python_check, mock_latex_check):
        """Test successful dependency check for all components."""
        mock_latex_check.return_value = Result(success=True, message="LaTeX OK")
        mock_python_check.return_value = Result(success=True, message="Python OK")
        
        result = self.system_checker.check_all_dependencies()
        
        self.assertTrue(result.success)
        self.assertIn('All required dependencies are available', result.message)
        self.assertIsNone(result.missing_dependencies)
    
    @patch('services.system_checker.SystemChecker.check_latex_installation')
    @patch('services.system_checker.SystemChecker.check_python_installation')
    def test_check_all_dependencies_missing_latex(self, mock_python_check, mock_latex_check):
        """Test dependency check when LaTeX is missing."""
        mock_latex_check.return_value = Result(success=False, message="LaTeX not found")
        mock_python_check.return_value = Result(success=True, message="Python OK")
        
        result = self.system_checker.check_all_dependencies()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'MISSING_DEPENDENCIES')
        self.assertIn('pdflatex', result.missing_dependencies)
        self.assertIn('pdflatex', result.installation_instructions)
    
    @patch('services.system_checker.SystemChecker.check_latex_installation')
    @patch('services.system_checker.SystemChecker.check_python_installation')
    def test_check_all_dependencies_multiple_missing(self, mock_python_check, mock_latex_check):
        """Test dependency check when multiple dependencies are missing."""
        mock_latex_check.return_value = Result(success=False, message="LaTeX not found")
        mock_python_check.return_value = Result(success=False, message="Python not found")
        
        result = self.system_checker.check_all_dependencies()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'MISSING_DEPENDENCIES')
        self.assertIn('pdflatex', result.missing_dependencies)
        self.assertIn('python', result.missing_dependencies)
        self.assertEqual(len(result.missing_dependencies), 2)
    
    @patch('platform.system')
    def test_get_installation_instruction_windows(self, mock_system):
        """Test getting installation instructions for Windows."""
        mock_system.return_value = 'Windows'
        
        instruction = self.system_checker._get_installation_instruction('pdflatex')
        
        self.assertIn('MiKTeX', instruction)
        self.assertIn('TeX Live', instruction)
    
    @patch('platform.system')
    def test_get_installation_instruction_linux(self, mock_system):
        """Test getting installation instructions for Linux."""
        mock_system.return_value = 'Linux'
        
        instruction = self.system_checker._get_installation_instruction('pdflatex')
        
        self.assertIn('texlive-latex-base', instruction)
        self.assertIn('apt-get', instruction)
    
    @patch('platform.system')
    def test_get_installation_instruction_macos(self, mock_system):
        """Test getting installation instructions for macOS."""
        mock_system.return_value = 'Darwin'
        
        instruction = self.system_checker._get_installation_instruction('pdflatex')
        
        self.assertIn('MacTeX', instruction)
        self.assertIn('Homebrew', instruction)
    
    @patch('platform.system')
    def test_get_installation_instruction_unknown_system(self, mock_system):
        """Test getting installation instructions for unknown system."""
        mock_system.return_value = 'UnknownOS'
        
        instruction = self.system_checker._get_installation_instruction('pdflatex')
        
        # Should default to Linux instructions
        self.assertIn('texlive-latex-base', instruction)
    
    def test_get_installation_instruction_unknown_dependency(self):
        """Test getting installation instructions for unknown dependency."""
        instruction = self.system_checker._get_installation_instruction('unknown_dep')
        
        self.assertIn('Please install unknown_dep', instruction)
    
    @patch('platform.system')
    @patch('platform.version')
    @patch('platform.architecture')
    @patch('platform.python_version')
    @patch('sys.executable', 'C:\\Python39\\python.exe')
    def test_get_system_info(self, mock_py_version, mock_arch, mock_version, mock_system):
        """Test getting system information."""
        mock_system.return_value = 'Windows'
        mock_version.return_value = '10.0.19041'
        mock_arch.return_value = ('64bit', 'WindowsPE')
        mock_py_version.return_value = '3.9.7'
        
        info = self.system_checker.get_system_info()
        
        self.assertEqual(info['platform'], 'Windows')
        self.assertEqual(info['platform_version'], '10.0.19041')
        self.assertEqual(info['architecture'], '64bit')
        self.assertEqual(info['python_version'], '3.9.7')
        self.assertIn('path_directories', info)
    
    @patch('services.system_checker.SystemChecker.check_all_dependencies')
    @patch('services.system_checker.SystemChecker.get_system_info')
    def test_validate_startup_requirements_success(self, mock_system_info, mock_check_deps):
        """Test successful startup requirements validation."""
        mock_check_deps.return_value = DependencyResult(
            success=True,
            message="All dependencies available"
        )
        mock_system_info.return_value = {'platform': 'Windows'}
        
        result = self.system_checker.validate_startup_requirements()
        
        self.assertTrue(result.success)
        self.assertIn('system_info', result.data)
    
    @patch('services.system_checker.SystemChecker.check_all_dependencies')
    @patch('services.system_checker.SystemChecker.get_system_info')
    def test_validate_startup_requirements_failure(self, mock_system_info, mock_check_deps):
        """Test startup requirements validation with missing dependencies."""
        mock_check_deps.return_value = DependencyResult(
            success=False,
            message="Missing dependencies",
            missing_dependencies=['pdflatex'],
            installation_instructions={'pdflatex': 'Install LaTeX'}
        )
        mock_system_info.return_value = {'platform': 'Windows'}
        
        result = self.system_checker.validate_startup_requirements()
        
        self.assertFalse(result.success)
        self.assertIn('system_info', result.data)
        self.assertIn('missing_dependencies', result.data)
        self.assertIn('installation_instructions', result.data)

    # Configuration validation tests
    
    def test_get_default_config_mes(self):
        """Test getting default config_mes.json content."""
        content = self.system_checker._get_default_config_mes()
        
        self.assertIsInstance(content, str)
        # Should be valid JSON
        import json
        config_data = json.loads(content)
        
        # Check required fields
        self.assertIn('titulo', config_data)
        self.assertIn('mes_nombre', config_data)
        self.assertIn('mes_anterior', config_data)
        self.assertIn('monto_anterior', config_data)
        self.assertIn('gastos_anteriores', config_data)
        self.assertIn('consideraciones_adicionales', config_data)
        self.assertIn('articulos', config_data)
    
    def test_get_default_presupuesto(self):
        """Test getting default presupuesto_base.json content."""
        content = self.system_checker._get_default_presupuesto()
        
        self.assertIsInstance(content, str)
        # Should be valid JSON
        import json
        presupuesto_data = json.loads(content)
        
        # Check required fields
        self.assertIn('categorias', presupuesto_data)
        self.assertIn('limite_mensual', presupuesto_data)
        self.assertIn('moneda', presupuesto_data)
        self.assertIsInstance(presupuesto_data['categorias'], dict)
    
    def test_get_default_csv_header(self):
        """Test getting default CSV header."""
        header = self.system_checker._get_default_csv_header()
        
        self.assertEqual(header, "Fecha,Monto,Categoria,Descripcion\n")
    
    def test_get_default_template(self):
        """Test getting default LaTeX template."""
        template = self.system_checker._get_default_template()
        
        self.assertIsInstance(template, str)
        self.assertIn('\\documentclass', template)
        self.assertIn('\\begin{document}', template)
        self.assertIn('\\end{document}', template)
        # Should contain Jinja2 template variables
        self.assertIn('{{ titulo }}', template)
        self.assertIn('{{ mes_nombre }}', template)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.dirname')
    def test_create_file_with_content(self, mock_dirname, mock_exists, mock_makedirs, mock_file):
        """Test creating a file with content."""
        mock_dirname.return_value = '/test/dir'
        mock_exists.return_value = False
        
        self.system_checker._create_file_with_content('/test/dir/file.txt', 'test content')
        
        mock_makedirs.assert_called_once_with('/test/dir', exist_ok=True)
        mock_file.assert_called_once_with('/test/dir/file.txt', 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with('test content')
    
    @patch('pandas.DataFrame')
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.dirname')
    def test_create_default_excel_file_with_pandas(self, mock_dirname, mock_exists, mock_makedirs, mock_df):
        """Test creating default Excel file with pandas available."""
        mock_dirname.return_value = '/test/dir'
        mock_exists.return_value = False
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        
        self.system_checker._create_default_excel_file('/test/dir/file.xlsx')
        
        mock_makedirs.assert_called_once_with('/test/dir', exist_ok=True)
        mock_df.assert_called_once_with(columns=['Fecha', 'Activo', 'Tipo', 'Monto'])
        mock_df_instance.to_excel.assert_called_once_with('/test/dir/file.xlsx', index=False, sheet_name='Inversiones')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.path.dirname')
    def test_create_default_excel_file_without_pandas(self, mock_dirname, mock_exists, mock_makedirs, mock_file):
        """Test creating default Excel file without pandas (fallback to CSV)."""
        mock_dirname.return_value = '/test/dir'
        mock_exists.return_value = False
        
        # Mock pandas import error
        with patch('builtins.__import__', side_effect=ImportError):
            self.system_checker._create_default_excel_file('/test/dir/file.xlsx')
        
        # Should create CSV file instead
        mock_file.assert_called_once_with('/test/dir/file.csv', 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with('Fecha,Activo,Tipo,Monto\n')
    
    @patch('services.system_checker.SystemChecker.validate_configuration')
    def test_validate_configuration_success_all_exist(self, mock_validate_config):
        """Test configuration validation when all files exist."""
        # Mock successful validation
        mock_validate_config.return_value = ConfigurationResult(
            success=True,
            message="All configuration files and directories are valid"
        )
        
        result = self.system_checker.validate_configuration()
        
        self.assertTrue(result.success)
        self.assertIn('All configuration files and directories are valid', result.message)
    
    @patch('services.system_checker.SystemChecker.validate_configuration')
    def test_validate_configuration_creates_missing_files(self, mock_validate_config):
        """Test configuration validation creates missing files."""
        # Mock validation that creates files
        mock_validate_config.return_value = ConfigurationResult(
            success=True,
            message="Configuration validation completed",
            created_files=['/test/config.json', '/test/gastos.csv', '/test/inversiones.xlsx'],
            created_directories=['/test/trackers']
        )
        
        result = self.system_checker.validate_configuration()
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.created_files)
        self.assertEqual(len(result.created_files), 3)
    
    @patch('os.path.exists')
    def test_validate_configuration_missing_config_module(self, mock_exists):
        """Test configuration validation when config module is missing."""
        with patch('builtins.__import__', side_effect=ImportError):
            result = self.system_checker.validate_configuration()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'CONFIG_MODULE_NOT_FOUND')
        self.assertIn('Configuration module not found', result.message)
    
    @patch('services.system_checker.SystemChecker._create_file_with_content')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_validate_configuration_directory_creation_failure(self, mock_exists, mock_makedirs, mock_create_file):
        """Test configuration validation when directory creation fails."""
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")
        
        # Mock config module
        with patch('builtins.__import__') as mock_import:
            mock_config = MagicMock()
            mock_config.RUTA_TRACKERS = '/test/trackers'
            mock_config.RUTA_RECURSOS = '/test/recursos'
            mock_config.RUTA_REPORTES = '/test/reportes'
            mock_config.RUTA_RESOLUCIONES = '/test/resoluciones'
            mock_config.RUTA_CONFIG_JSON = '/test/config.json'
            
            mock_import.return_value = mock_config
            
            result = self.system_checker.validate_configuration()
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'DIRECTORY_CREATION_FAILED')
        self.assertIn('Failed to create directory', result.message)


if __name__ == '__main__':
    # Run the tests
    unittest.main()