# -*- coding: utf-8 -*-
"""
PDF generation utilities for the PECO application.
Handles LaTeX compilation, template processing, and PDF generation with comprehensive error handling.
"""

import os
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .exceptions import LaTeXError, ConfigurationError
from .latex_processor import LaTeXProcessor
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PDFResult:
    """Result object for PDF generation operations."""
    success: bool
    message: str
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    compilation_log: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class CompilationResult:
    """Result object for LaTeX compilation operations."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    pdf_created: bool = False


class PDFGenerator:
    """
    Handles PDF generation from LaTeX templates with comprehensive error handling.
    
    This class provides robust PDF generation capabilities including:
    - LaTeX dependency checking
    - Template processing with character escaping
    - PDF compilation with detailed error reporting
    - Automatic cleanup of temporary files
    """
    
    def __init__(self, latex_processor: Optional[LaTeXProcessor] = None):
        """
        Initialize PDF generator.
        
        Args:
            latex_processor: LaTeX processor instance for character escaping.
                           If None, creates a new instance.
        """
        self.latex_processor = latex_processor or LaTeXProcessor()
        logger.debug("PDF generator initialized")
    
    def check_latex_availability(self) -> bool:
        """
        Check if pdflatex is available on the system.
        
        Returns:
            True if pdflatex is available, False otherwise
        """
        try:
            logger.debug("Checking pdflatex availability")
            result = subprocess.run(
                ['pdflatex', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            available = result.returncode == 0
            if available:
                logger.info("pdflatex is available")
                logger.debug(f"pdflatex version info: {result.stdout.split(chr(10))[0]}")
            else:
                logger.warning("pdflatex is not available or not working properly")
                
            return available
            
        except FileNotFoundError:
            logger.warning("pdflatex command not found")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("pdflatex version check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking pdflatex availability: {e}")
            return False
    
    def compile_to_pdf(self, tex_file: str, output_dir: str) -> CompilationResult:
        """
        Compile LaTeX file to PDF using pdflatex.
        
        Args:
            tex_file: Path to the .tex file to compile
            output_dir: Directory where PDF should be generated
            
        Returns:
            CompilationResult with compilation details
            
        Raises:
            LaTeXError: If compilation fails or pdflatex is not available
        """
        if not self.check_latex_availability():
            raise LaTeXError(
                "pdflatex is not available. Please install a LaTeX distribution.",
                details={
                    'suggestion': 'Install MiKTeX or TeX Live for Windows',
                    'tex_file': tex_file
                }
            )
        
        if not os.path.exists(tex_file):
            raise LaTeXError(
                f"LaTeX file not found: {tex_file}",
                details={'tex_file': tex_file}
            )
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            logger.info(f"Compiling LaTeX file: {tex_file}")
            logger.debug(f"Output directory: {output_dir}")
            
            # Run pdflatex compilation with non-interactive mode
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=60  # 60 second timeout
            )
            
            # Check if PDF was created
            tex_basename = os.path.splitext(os.path.basename(tex_file))[0]
            expected_pdf = os.path.join(output_dir, f"{tex_basename}.pdf")
            pdf_created = os.path.exists(expected_pdf)
            
            # LaTeX compilation is considered successful if:
            # 1. PDF file was created, OR
            # 2. Return code is 0 (no errors, only warnings)
            # LaTeX can have warnings (return code 1) but still produce a valid PDF
            compilation_successful = pdf_created or process.returncode == 0
            
            result = CompilationResult(
                success=compilation_successful,
                stdout=process.stdout,
                stderr=process.stderr,
                return_code=process.returncode,
                pdf_created=pdf_created
            )
            
            if result.success:
                logger.info(f"PDF compilation successful: {expected_pdf}")
            else:
                logger.error(f"PDF compilation failed. Return code: {process.returncode}")
                logger.error(f"Stdout: {process.stdout}")
                logger.error(f"Stderr: {process.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error("LaTeX compilation timed out")
            raise LaTeXError(
                "LaTeX compilation timed out after 60 seconds",
                details={'tex_file': tex_file, 'timeout': 60}
            )
        except Exception as e:
            logger.error(f"Error during LaTeX compilation: {e}")
            raise LaTeXError(
                f"LaTeX compilation failed: {str(e)}",
                details={'tex_file': tex_file, 'error': str(e)}
            )    

    def process_template(self, template_path: str, data: Dict[str, Any]) -> str:
        """
        Process Jinja2 template with LaTeX-safe data.
        
        Args:
            template_path: Path to the template file
            data: Data dictionary for template rendering
            
        Returns:
            Rendered template content with escaped characters
            
        Raises:
            LaTeXError: If template processing fails
            ConfigurationError: If template file is not found or not readable
        """
        # Validate template file existence
        if not os.path.exists(template_path):
            raise ConfigurationError(
                f"Template file not found: {template_path}",
                details={'template_path': template_path}
            )
        
        # Validate template file readability
        if not os.access(template_path, os.R_OK):
            raise ConfigurationError(
                f"Template file is not readable: {template_path}",
                details={'template_path': template_path, 'permissions': 'read access denied'}
            )
        
        # Validate template file is actually a file (not a directory)
        if not os.path.isfile(template_path):
            raise ConfigurationError(
                f"Template path is not a file: {template_path}",
                details={'template_path': template_path, 'type': 'not a regular file'}
            )
        
        try:
            logger.debug(f"Processing template: {template_path}")
            

            # Set up Jinja2 environment
            template_dir = os.path.dirname(template_path) if os.path.dirname(template_path) else '.'
            template_name = os.path.basename(template_path)
            
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(template_name)
            
            # Process data to escape special characters
            processed_data = self._process_template_data(data)
            
            # Render template
            rendered_content = template.render(processed_data)
            
            logger.debug("Template processing completed successfully")
            return rendered_content
            
        except TemplateNotFound:
            raise ConfigurationError(
                f"Template not found: {template_name}",
                details={'template_path': template_path, 'template_dir': template_dir}
            )
        except Exception as e:
            logger.error(f"Template processing failed: {e}")
            raise LaTeXError(
                f"Template processing failed: {str(e)}",
                details={'template_path': template_path, 'error': str(e)}
            )
    
    def _process_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process template data to escape special characters for LaTeX.
        
        Args:
            data: Raw template data
            
        Returns:
            Processed data with escaped strings
        """
        processed = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Escape special characters in string values
                processed[key] = self.latex_processor.escape_special_characters(value)
            elif isinstance(value, list):
                # Process list items
                processed[key] = self._process_list_data(value)
            elif isinstance(value, dict):
                # Recursively process dictionary values
                processed[key] = self._process_template_data(value)
            else:
                # Keep other types as-is (numbers, booleans, etc.)
                processed[key] = value
        
        return processed
    
    def _process_list_data(self, data_list: List[Any]) -> List[Any]:
        """
        Process list data to escape special characters.
        
        Args:
            data_list: List containing various data types
            
        Returns:
            Processed list with escaped strings
        """
        processed_list = []
        
        for item in data_list:
            if isinstance(item, str):
                processed_list.append(self.latex_processor.escape_special_characters(item))
            elif isinstance(item, dict):
                processed_list.append(self._process_template_data(item))
            elif isinstance(item, list):
                processed_list.append(self._process_list_data(item))
            else:
                processed_list.append(item)
        
        return processed_list
    
    def generate_resolution(self, template_path: str, data: Dict[str, Any], 
                          output_dir: str, filename_base: str) -> PDFResult:
        """
        Generate a resolution PDF from template and data.
        
        Args:
            template_path: Path to the LaTeX template file
            data: Data dictionary for template rendering
            output_dir: Directory where files should be generated
            filename_base: Base filename (without extension)
            
        Returns:
            PDFResult with generation details
        """
        try:
            logger.info(f"Starting PDF generation for: {filename_base}")
            
            # Ensure output directory structure is valid and accessible
            try:
                self.ensure_directory_structure(output_dir)
            except ConfigurationError as e:
                return PDFResult(
                    success=False,
                    message=f"Directory validation failed: {str(e)}",
                    error_code="DIRECTORY_ERROR",
                    details=e.details
                )
            
            # Process template
            try:
                tex_content = self.process_template(template_path, data)
            except Exception as e:
                return PDFResult(
                    success=False,
                    message=f"Template processing failed: {str(e)}",
                    error_code="TEMPLATE_ERROR",
                    details={'template_path': template_path, 'error': str(e)}
                )
            
            # Copy required resource files to output directory
            try:
                resource_copy_result = self._copy_template_resources(template_path, output_dir)
                logger.debug(f"Resource copy result: {resource_copy_result}")
            except Exception as e:
                logger.warning(f"Failed to copy some template resources: {e}")
                # Don't fail the entire process, just log the warning
            
            # Write .tex file
            tex_path = os.path.join(output_dir, f"{filename_base}.tex")
            try:
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(tex_content)
                logger.debug(f"LaTeX file written: {tex_path}")
            except Exception as e:
                return PDFResult(
                    success=False,
                    message=f"Failed to write LaTeX file: {str(e)}",
                    error_code="FILE_WRITE_ERROR",
                    details={'tex_path': tex_path, 'error': str(e)}
                )
            
            # Compile to PDF
            try:
                compilation_result = self.compile_to_pdf(tex_path, output_dir)
            except LaTeXError as e:
                return PDFResult(
                    success=False,
                    message=str(e),
                    tex_path=tex_path,
                    error_code="COMPILATION_ERROR",
                    details=e.details
                )
            
            # Check compilation result
            pdf_path = os.path.join(output_dir, f"{filename_base}.pdf")
            
            if compilation_result.success:
                logger.info(f"PDF generation successful: {pdf_path}")
                
                # Automatically clean temporary files after successful compilation
                base_path = os.path.join(output_dir, filename_base)
                cleanup_result = self.clean_temp_files(base_path)
                
                return PDFResult(
                    success=True,
                    message="PDF generated successfully",
                    pdf_path=pdf_path,
                    tex_path=tex_path,
                    compilation_log=compilation_result.stdout,
                    details={'cleanup_result': cleanup_result}
                )
            else:
                error_msg = "PDF compilation failed"
                if compilation_result.stderr:
                    error_msg += f": {compilation_result.stderr}"
                
                return PDFResult(
                    success=False,
                    message=error_msg,
                    tex_path=tex_path,
                    compilation_log=compilation_result.stdout,
                    error_code="COMPILATION_FAILED",
                    details={
                        'return_code': compilation_result.return_code,
                        'stdout': compilation_result.stdout,
                        'stderr': compilation_result.stderr
                    }
                )
                
        except Exception as e:
            logger.error(f"Unexpected error during PDF generation: {e}")
            return PDFResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                details={'error': str(e)}
            )
    
    def clean_temp_files(self, base_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Clean temporary files generated during LaTeX compilation.
        
        Args:
            base_path: Base path (without extension) of the files to clean
            extensions: List of extensions to clean. Defaults to ['.aux', '.log']
            
        Returns:
            Dictionary with cleanup results including success count and errors
        """
        if extensions is None:
            extensions = ['.aux', '.log', '.fls', '.fdb_latexmk', '.synctex.gz']
        
        logger.debug(f"Cleaning temporary files for: {base_path}")
        
        cleaned_files = []
        failed_files = []
        permission_errors = []
        
        for ext in extensions:
            file_path = base_path + ext
            try:
                if os.path.exists(file_path):
                    # Check if we have permission to delete the file
                    if not os.access(file_path, os.W_OK):
                        permission_errors.append(os.path.basename(file_path))
                        logger.warning(f"No write permission for file: {file_path}")
                        continue
                    
                    os.remove(file_path)
                    cleaned_files.append(os.path.basename(file_path))
                    logger.debug(f"Removed temporary file: {file_path}")
            except PermissionError as e:
                permission_errors.append(os.path.basename(file_path))
                logger.warning(f"Permission denied removing {file_path}: {e}")
            except Exception as e:
                failed_files.append((os.path.basename(file_path), str(e)))
                logger.warning(f"Failed to remove {file_path}: {e}")
        
        result = {
            'cleaned_files': cleaned_files,
            'failed_files': failed_files,
            'permission_errors': permission_errors,
            'total_cleaned': len(cleaned_files),
            'total_failed': len(failed_files) + len(permission_errors)
        }
        
        if cleaned_files:
            logger.info(f"Cleaned temporary files: {', '.join(cleaned_files)}")
        
        if failed_files or permission_errors:
            logger.warning(f"Failed to clean some files: {failed_files + permission_errors}")
        
        return result
    
    def ensure_directory_structure(self, output_dir: str) -> bool:
        """
        Ensure that the output directory structure exists and is writable.
        
        Args:
            output_dir: Directory path to validate and create if necessary
            
        Returns:
            True if directory is ready for use, False otherwise
            
        Raises:
            ConfigurationError: If directory cannot be created or accessed
        """
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(output_dir):
                logger.debug(f"Creating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
            
            # Validate directory exists and is actually a directory
            if not os.path.isdir(output_dir):
                raise ConfigurationError(
                    f"Output path exists but is not a directory: {output_dir}",
                    details={'path': output_dir, 'type': 'not a directory'}
                )
            
            # Check write permissions
            if not os.access(output_dir, os.W_OK):
                raise ConfigurationError(
                    f"No write permission for output directory: {output_dir}",
                    details={'path': output_dir, 'permissions': 'write access denied'}
                )
            
            # Check read permissions
            if not os.access(output_dir, os.R_OK):
                raise ConfigurationError(
                    f"No read permission for output directory: {output_dir}",
                    details={'path': output_dir, 'permissions': 'read access denied'}
                )
            
            logger.debug(f"Directory structure validated: {output_dir}")
            return True
            
        except OSError as e:
            logger.error(f"Failed to create or access directory {output_dir}: {e}")
            raise ConfigurationError(
                f"Cannot create or access output directory: {str(e)}",
                details={'path': output_dir, 'error': str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error validating directory {output_dir}: {e}")
            raise ConfigurationError(
                f"Directory validation failed: {str(e)}",
                details={'path': output_dir, 'error': str(e)}
            )
    
    def _copy_template_resources(self, template_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Copy required resource files (images, etc.) from template directory to output directory.
        
        This method scans the template for resource references and copies the required files
        to the output directory so LaTeX can find them during compilation.
        
        Args:
            template_path: Path to the template file
            output_dir: Directory where resources should be copied
            
        Returns:
            Dictionary with copy results including success count and errors
        """
        logger.debug(f"Copying template resources for: {template_path}")
        
        # Determine the template directory (where resources are located)
        template_dir = os.path.dirname(template_path)
        
        # List of resource files that the template typically needs
        # These are based on the known template structure
        resource_files = ['logo.png', 'firma.png']
        
        copied_files = []
        failed_files = []
        missing_files = []
        
        for resource_file in resource_files:
            source_path = os.path.join(template_dir, resource_file)
            dest_path = os.path.join(output_dir, resource_file)
            
            try:
                if os.path.exists(source_path):
                    # Copy the file to the output directory
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(resource_file)
                    logger.debug(f"Copied resource file: {resource_file}")
                else:
                    missing_files.append(resource_file)
                    logger.debug(f"Resource file not found: {source_path}")
            except Exception as e:
                failed_files.append((resource_file, str(e)))
                logger.warning(f"Failed to copy resource file {resource_file}: {e}")
        
        # Also create a subdirectory structure that matches the template's expectations
        # The template expects ../05_Templates_y_Recursos/logo.png
        # So we create a 05_Templates_y_Recursos subdirectory in the output directory
        try:
            resources_subdir = os.path.join(output_dir, "05_Templates_y_Recursos")
            os.makedirs(resources_subdir, exist_ok=True)
            
            # Copy files to the subdirectory as well
            for resource_file in resource_files:
                source_path = os.path.join(template_dir, resource_file)
                dest_path = os.path.join(resources_subdir, resource_file)
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    logger.debug(f"Copied resource file to subdirectory: {resource_file}")
                    
        except Exception as e:
            logger.warning(f"Failed to create resource subdirectory structure: {e}")
        
        result = {
            'copied_files': copied_files,
            'failed_files': failed_files,
            'missing_files': missing_files,
            'total_copied': len(copied_files),
            'total_failed': len(failed_files),
            'total_missing': len(missing_files)
        }
        
        if copied_files:
            logger.info(f"Copied template resources: {', '.join(copied_files)}")
        
        if failed_files:
            logger.warning(f"Failed to copy some resources: {[f[0] for f in failed_files]}")
        
        if missing_files:
            logger.info(f"Some template resources were not found: {missing_files}")
        
        return result
    
    def validate_file_permissions(self, file_path: str, required_permissions: str = 'rw') -> bool:
        """
        Validate file permissions for a given file path.
        
        Args:
            file_path: Path to the file to check
            required_permissions: String containing required permissions ('r', 'w', 'x')
            
        Returns:
            True if all required permissions are available, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        permissions_ok = True
        
        if 'r' in required_permissions and not os.access(file_path, os.R_OK):
            logger.warning(f"No read permission for file: {file_path}")
            permissions_ok = False
        
        if 'w' in required_permissions and not os.access(file_path, os.W_OK):
            logger.warning(f"No write permission for file: {file_path}")
            permissions_ok = False
        
        if 'x' in required_permissions and not os.access(file_path, os.X_OK):
            logger.warning(f"No execute permission for file: {file_path}")
            permissions_ok = False
        
        return permissions_ok