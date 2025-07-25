# PECO Service Layer Documentation

This document provides detailed documentation for the PECO service layer architecture, including all classes, methods, and error handling procedures.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Service Classes](#service-classes)
- [Error Handling System](#error-handling-system)
- [Result Pattern](#result-pattern)
- [Logging System](#logging-system)
- [Configuration Management](#configuration-management)
- [Best Practices](#best-practices)

## Architecture Overview

The PECO service layer follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Flask Web     │  │  CLI Scripts    │  │  Direct API │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  DataManager    │  │  PDFGenerator   │  │SystemChecker│ │
│  │                 │  │                 │  │             │ │
│  │ • Expenses      │  │ • LaTeX Proc    │  │ • Validation│ │
│  │ • Investments   │  │ • PDF Creation  │  │ • Dependencies│
│  │ • Analysis      │  │ • Cleanup       │  │ • Config    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   File System   │  │    Logging      │  │ Error Mgmt  │ │
│  │                 │  │                 │  │             │ │
│  │ • CSV Files     │  │ • File Logs     │  │ • Exceptions│ │
│  │ • Excel Files   │  │ • Console Logs  │  │ • Result    │ │
│  │ • JSON Config   │  │ • Log Rotation  │  │ • Recovery  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Single Responsibility**: Each service class has a specific, well-defined purpose
2. **Dependency Injection**: Services can be configured with different dependencies
3. **Result Pattern**: All operations return Result objects for consistent error handling
4. **Comprehensive Logging**: All operations are logged for debugging and monitoring
5. **Configuration-Driven**: Behavior is controlled through configuration files
6. **Error Recovery**: Services attempt to recover from common error conditions

## Service Classes

### DataManager

**Purpose**: Centralized data management for expenses, investments, and financial analysis.

**Location**: `services/data_manager.py`

**Dependencies**:
- `config` module for file paths
- `pandas` for data manipulation
- `csv` and `json` for file operations

#### Class Definition

```python
class DataManager:
    """
    Service class for managing financial data operations.
    Handles expense and investment registration, data validation, and analysis.
    """
    
    def __init__(self, config_module=None):
        """
        Initialize DataManager with configuration.
        
        Args:
            config_module: Configuration module with file paths
        """
```

#### Key Methods

##### register_expense
```python
def register_expense(self, amount: float, category: str, description: str) -> Result:
    """
    Register a new expense in the CSV file.
    
    Validation:
    - Amount must be > 0 and < 1,000,000 ARS
    - Category and description are required
    - Automatic date assignment
    
    File Operations:
    - Creates CSV file if it doesn't exist
    - Adds proper headers
    - Appends new expense record
    
    Error Handling:
    - Validates input data
    - Checks file permissions
    - Creates directories if needed
    """
```

##### register_investment
```python
def register_investment(self, asset: str, operation_type: str, amount: float) -> Result:
    """
    Register a new investment operation in the Excel file.
    
    Validation:
    - Amount must be > 0
    - Asset name is required
    - Operation type must be 'Compra' or 'Venta'
    
    File Operations:
    - Creates Excel file if it doesn't exist
    - Maintains proper column structure
    - Appends to existing data
    """
```

##### get_monthly_analysis
```python
def get_monthly_analysis(self, month: int, year: int) -> AnalysisResult:
    """
    Get comprehensive monthly financial analysis.
    
    Data Processing:
    - Loads and filters expense data by month/year
    - Loads and analyzes investment data
    - Calculates totals and breakdowns
    - Loads budget configuration
    
    Returns:
    - Total expenses and breakdown by category
    - Investment totals (purchases/sales)
    - Budget comparison data
    - Individual transaction records
    """
```

##### validate_data_integrity
```python
def validate_data_integrity(self) -> Result:
    """
    Validate the integrity of all data files.
    
    Checks:
    - File existence and readability
    - Proper column structure
    - Data type validation
    - Directory structure
    
    Recovery:
    - Reports specific issues found
    - Provides guidance for resolution
    """
```

#### Private Helper Methods

- `_validate_expense_data()`: Input validation for expenses
- `_validate_investment_data()`: Input validation for investments
- `_load_and_analyze_expenses()`: Load and process expense data
- `_load_and_analyze_investments()`: Load and process investment data
- `_validate_expenses_file()`: Validate CSV file structure
- `_validate_investments_file()`: Validate Excel file structure

### PDFGenerator

**Purpose**: Handles LaTeX compilation and PDF generation with comprehensive error handling.

**Location**: `services/pdf_generator.py`

**Dependencies**:
- `LaTeXProcessor` for character escaping
- `subprocess` for LaTeX compilation
- `jinja2` for template processing

#### Class Definition

```python
class PDFGenerator:
    """
    Handles PDF generation from LaTeX templates with comprehensive error handling.
    
    Features:
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
```

#### Key Methods

##### generate_resolution
```python
def generate_resolution(self, template_path: str, data: Dict[str, Any], 
                       output_dir: str, filename_base: str) -> PDFResult:
    """
    Generate a resolution PDF from template and data.
    
    Process:
    1. Validate directory structure
    2. Process template with escaped data
    3. Copy required resource files
    4. Write LaTeX file
    5. Compile to PDF
    6. Clean temporary files
    
    Error Handling:
    - Template validation
    - Directory creation
    - Compilation error parsing
    - Resource file management
    """
```

##### check_latex_availability
```python
def check_latex_availability(self) -> bool:
    """
    Check if pdflatex is available on the system.
    
    Process:
    - Runs 'pdflatex --version'
    - Validates return code
    - Logs version information
    - Handles timeouts and errors
    """
```

##### compile_to_pdf
```python
def compile_to_pdf(self, tex_file: str, output_dir: str) -> CompilationResult:
    """
    Compile LaTeX file to PDF using pdflatex.
    
    Features:
    - Non-interactive mode compilation
    - 60-second timeout protection
    - Detailed error logging
    - UTF-8 encoding handling
    - Return code interpretation
    """
```

##### clean_temp_files
```python
def clean_temp_files(self, base_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Clean temporary files generated during LaTeX compilation.
    
    Default Extensions:
    - .aux (auxiliary file)
    - .log (compilation log)
    - .fls (file list)
    - .fdb_latexmk (latexmk database)
    - .synctex.gz (synchronization file)
    
    Error Handling:
    - Permission checks
    - Individual file error tracking
    - Detailed cleanup reporting
    """
```

#### Private Helper Methods

- `_process_template_data()`: Recursively escape template data
- `_process_list_data()`: Handle list data escaping
- `_copy_template_resources()`: Copy required resource files
- `ensure_directory_structure()`: Validate and create directories

### LaTeXProcessor

**Purpose**: Handles character escaping and template processing for safe LaTeX compilation.

**Location**: `services/latex_processor.py`

**Dependencies**: None (standalone utility class)

#### Character Escape System

```python
LATEX_ESCAPE_MAP = {
    '$': r'\$',           # Currency symbol
    '%': r'\%',           # Percent sign
    '&': r'\&',           # Ampersand
    '#': r'\#',           # Hash symbol
    '_': r'\_',           # Underscore
    '{': r'\{',           # Opening brace
    '}': r'\}',           # Closing brace
    '^': r'\textasciicircum{}',    # Caret
    '~': r'\textasciitilde{}',     # Tilde
    '\\': r'\textbackslash{}',     # Backslash
    '*': r'\textasteriskcentered{}', # Asterisk
    '[': r'{[}',          # Opening bracket
    ']': r'{]}',          # Closing bracket
    '|': r'\textbar{}',   # Pipe
    '<': r'\textless{}',  # Less than
    '>': r'\textgreater{}' # Greater than
}
```

#### Key Methods

##### escape_special_characters
```python
def escape_special_characters(self, text: str) -> str:
    """
    Escape special characters in text to make it safe for LaTeX processing.
    
    Algorithm:
    1. Replace backslashes with placeholder
    2. Process all other special characters
    3. Replace placeholder with proper backslash escape
    
    This prevents double-escaping issues.
    """
```

##### process_description
```python
def process_description(self, description: str) -> str:
    """
    Process expense/investment descriptions for safe LaTeX inclusion.
    
    Uses general character escaping to handle all special characters
    including currency symbols, mathematical operators, and markup.
    """
```

##### validate_escaped_text
```python
def validate_escaped_text(self, text: str) -> bool:
    """
    Validate that text has been properly escaped for LaTeX.
    
    Checks for common problematic patterns:
    - Unescaped dollar signs
    - Unescaped percent signs
    - Unescaped ampersands
    - Other problematic characters
    """
```

### SystemChecker

**Purpose**: Validates system dependencies and configuration, provides installation guidance.

**Location**: `services/system_checker.py`

**Dependencies**:
- `subprocess` for dependency checking
- `json` for configuration validation
- `pandas` for Excel file operations

#### Key Methods

##### validate_complete_system
```python
def validate_complete_system(self) -> DependencyResult:
    """
    Perform complete system validation including dependencies and configuration.
    
    Validation Steps:
    1. Check system dependencies (pdflatex, Python)
    2. Validate configuration files
    3. Create missing directories and files
    4. Provide installation instructions for missing components
    
    Returns comprehensive result with system info and remediation steps.
    """
```

##### check_latex_installation
```python
def check_latex_installation(self) -> Result:
    """
    Check if pdflatex is available in the system.
    
    Process:
    - Checks if pdflatex is in PATH
    - Runs version check with timeout
    - Validates functionality
    - Provides platform-specific installation instructions
    """
```

##### validate_configuration
```python
def validate_configuration(self) -> ConfigurationResult:
    """
    Validate all configuration files and directories, creating missing ones.
    
    Validation:
    - Required directories exist and are writable
    - Configuration files have proper structure
    - Template files are available
    - Resource files are present
    
    Auto-Creation:
    - Missing directories
    - Default configuration files
    - Empty data files with proper structure
    """
```

#### Installation Instructions

The SystemChecker provides platform-specific installation instructions:

```python
INSTALLATION_INSTRUCTIONS = {
    'pdflatex': {
        'windows': 'Install MiKTeX from https://miktex.org/download or TeX Live from https://www.tug.org/texlive/',
        'linux': 'Install texlive-latex-base: sudo apt-get install texlive-latex-base texlive-latex-extra',
        'macos': 'Install MacTeX from https://www.tug.org/mactex/ or use Homebrew: brew install --cask mactex'
    }
}
```

## Error Handling System

### Exception Hierarchy

```python
class PECOError(Exception):
    """Base exception class for all PECO-related errors."""
    def __init__(self, message: str, error_code: str = None, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class LaTeXError(PECOError):
    """Exception for LaTeX-related errors."""
    pass

class DataError(PECOError):
    """Exception for data-related errors."""
    pass

class ConfigurationError(PECOError):
    """Exception for configuration-related errors."""
    pass
```

### Error Codes

Common error codes used throughout the system:

- **LATEX_NOT_FOUND**: pdflatex not available
- **LATEX_COMPILATION_ERROR**: LaTeX compilation failed
- **FILE_NOT_FOUND**: Required file missing
- **PERMISSION_DENIED**: Insufficient file permissions
- **INVALID_DATA**: Data validation failed
- **CONFIGURATION_ERROR**: Configuration file issues
- **DEPENDENCY_MISSING**: Required dependency not available

### Error Recovery Strategies

1. **Automatic Directory Creation**: Missing directories are created automatically
2. **Default File Generation**: Missing configuration files are created with defaults
3. **Graceful Degradation**: System continues to function with reduced capabilities
4. **Detailed Error Messages**: Specific guidance for resolving issues
5. **Installation Instructions**: Platform-specific dependency installation guidance

## Result Pattern

All service methods return Result objects for consistent error handling:

### Base Result Class

```python
@dataclass
class Result:
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
```

### Specialized Result Classes

```python
@dataclass
class PDFResult(Result):
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    compilation_log: Optional[str] = None

@dataclass
class AnalysisResult(Result):
    total_expenses: float = 0.0
    expenses_by_category: Dict[str, float] = None
    total_investments: float = 0.0
    analysis_data: Optional[Dict[str, Any]] = None

@dataclass
class DependencyResult(Result):
    missing_dependencies: Optional[List[str]] = None
    installation_instructions: Optional[Dict[str, str]] = None
```

### Usage Pattern

```python
# Service method call
result = service.method()

# Check success
if result.success:
    # Handle success case
    data = result.data
    print(result.message)
else:
    # Handle error case
    print(f"Error: {result.message}")
    if result.error_code:
        # Handle specific error types
        if result.error_code == "FILE_NOT_FOUND":
            # Specific recovery action
            pass
```

## Logging System

### Configuration

**Location**: `services/logging_config.py`

**Features**:
- File and console logging
- Log rotation (10MB files, 5 backups)
- UTF-8 encoding support
- Configurable log levels
- Structured log format

### Logger Setup

```python
def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
```

### Log Format

```
2025-07-24 10:30:45 - peco.data_manager - INFO - data_manager.py:123 - Expense registered successfully
```

### Usage in Services

```python
from .logging_config import get_logger

logger = get_logger(__name__)

def service_method(self):
    logger.info("Starting operation")
    try:
        # Operation logic
        logger.debug("Operation details")
        logger.info("Operation completed successfully")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

## Configuration Management

### Configuration Structure

**Location**: `config.py`

**Sections**:
- **Paths**: File and directory locations
- **Service Configuration**: Settings for each service
- **Environment-Specific**: Development/testing/production settings
- **Validation**: Configuration validation functions

### Service Configurations

```python
# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "max_file_size": 10 * 1024 * 1024,
    "backup_count": 5,
    "console_level": "INFO",
    "file_level": "DEBUG"
}

# PDF Generation Configuration
PDF_CONFIG = {
    "latex_timeout": 60,
    "temp_file_extensions": ['.aux', '.log', '.fls', '.fdb_latexmk', '.synctex.gz'],
    "auto_cleanup": True,
    "resource_files": ["logo.png", "firma.png"],
    "compilation_retries": 1
}

# Data Manager Configuration
DATA_CONFIG = {
    "csv_encoding": "utf-8",
    "excel_sheet_name": "Inversiones",
    "date_format": "%Y-%m-%d",
    "max_amount_threshold": 1000000,
    "backup_enabled": False,
    "validation_enabled": True
}
```

### Environment-Specific Configuration

```python
def get_config_for_environment(env: Optional[str] = None) -> Dict[str, Any]:
    """
    Get configuration settings for specific environment.
    
    Environments:
    - development: Debug mode, verbose logging
    - testing: Minimal logging, testing optimizations
    - production: Optimized for regular use
    """
```

## Best Practices

### Service Implementation

1. **Constructor Dependency Injection**:
   ```python
   def __init__(self, config_module=None, logger=None):
       self.config = config_module or default_config
       self.logger = logger or get_logger(__name__)
   ```

2. **Result Pattern Usage**:
   ```python
   def service_method(self) -> Result:
       try:
           # Operation logic
           return Result(success=True, message="Success", data=result_data)
       except SpecificError as e:
           return Result(success=False, message=str(e), error_code="SPECIFIC_ERROR")
   ```

3. **Comprehensive Logging**:
   ```python
   logger.info("Starting operation with parameters: %s", params)
   logger.debug("Intermediate step completed")
   logger.error("Operation failed: %s", error_message)
   ```

4. **Input Validation**:
   ```python
   def validate_input(self, data) -> Result:
       if not data:
           return Result(success=False, message="Data is required", error_code="MISSING_DATA")
       # Additional validation
       return Result(success=True, message="Valid")
   ```

### Error Handling

1. **Specific Exception Types**:
   ```python
   try:
       # Operation
   except FileNotFoundError:
       raise ConfigurationError("Required file not found", error_code="FILE_NOT_FOUND")
   except PermissionError:
       raise ConfigurationError("Permission denied", error_code="PERMISSION_DENIED")
   ```

2. **Error Recovery**:
   ```python
   try:
       # Primary operation
   except RecoverableError:
       logger.warning("Primary operation failed, attempting recovery")
       # Recovery logic
   ```

3. **Detailed Error Information**:
   ```python
   raise LaTeXError(
       "LaTeX compilation failed",
       error_code="COMPILATION_ERROR",
       details={
           'tex_file': tex_file,
           'return_code': process.returncode,
           'stderr': process.stderr
       }
   )
   ```

### Testing Services

1. **Mock External Dependencies**:
   ```python
   @patch('subprocess.run')
   def test_latex_compilation(self, mock_run):
       mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
       # Test logic
   ```

2. **Test Result Objects**:
   ```python
   result = service.method()
   self.assertTrue(result.success)
   self.assertEqual(result.error_code, "EXPECTED_CODE")
   ```

3. **Test Error Conditions**:
   ```python
   with self.assertRaises(SpecificError):
       service.method_that_should_fail()
   ```

This service layer provides a robust foundation for the PECO application with comprehensive error handling, logging, and configuration management.