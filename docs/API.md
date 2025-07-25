# PECO API Reference

This document provides comprehensive API documentation for all service classes and methods in the PECO financial management system.

## Table of Contents

- [DataManager](#datamanager)
- [PDFGenerator](#pdfgenerator)
- [LaTeXProcessor](#latexprocessor)
- [SystemChecker](#systemchecker)
- [Result Classes](#result-classes)
- [Exception Classes](#exception-classes)
- [Configuration](#configuration)

## DataManager

The `DataManager` class provides centralized data management for expenses and investments.

### Constructor

```python
DataManager(config_module=None)
```

**Parameters:**
- `config_module` (optional): Configuration module with file paths. Defaults to the main config module.

### Methods

#### register_expense

```python
register_expense(amount: float, category: str, description: str) -> Result
```

Register a new expense in the CSV file.

**Parameters:**
- `amount` (float): Expense amount in ARS
- `category` (str): Expense category
- `description` (str): Expense description

**Returns:**
- `Result`: Object indicating success or failure with expense data

**Example:**
```python
dm = DataManager()
result = dm.register_expense(1500.0, "Comida", "Almuerzo en restaurante")
if result.success:
    print(f"Expense registered: {result.data}")
else:
    print(f"Error: {result.message}")
```

#### register_investment

```python
register_investment(asset: str, operation_type: str, amount: float) -> Result
```

Register a new investment operation in the Excel file.

**Parameters:**
- `asset` (str): Asset ticker or name
- `operation_type` (str): 'Compra' or 'Venta'
- `amount` (float): Operation amount in ARS

**Returns:**
- `Result`: Object indicating success or failure with investment data

**Example:**
```python
result = dm.register_investment("AAPL", "Compra", 50000.0)
```

#### get_monthly_analysis

```python
get_monthly_analysis(month: int, year: int) -> AnalysisResult
```

Get comprehensive monthly financial analysis.

**Parameters:**
- `month` (int): Month number (1-12)
- `year` (int): Year

**Returns:**
- `AnalysisResult`: Analysis data including expenses and investments

**Example:**
```python
analysis = dm.get_monthly_analysis(7, 2025)
if analysis.success:
    print(f"Total expenses: {analysis.total_expenses}")
    print(f"By category: {analysis.expenses_by_category}")
```

#### validate_data_integrity

```python
validate_data_integrity() -> Result
```

Validate the integrity of all data files.

**Returns:**
- `Result`: Validation status with any issues found

## PDFGenerator

The `PDFGenerator` class handles LaTeX compilation and PDF generation.

### Constructor

```python
PDFGenerator(latex_processor: Optional[LaTeXProcessor] = None)
```

**Parameters:**
- `latex_processor` (optional): LaTeX processor instance. Creates new instance if None.

### Methods

#### generate_resolution

```python
generate_resolution(template_path: str, data: Dict[str, Any], 
                   output_dir: str, filename_base: str) -> PDFResult
```

Generate a resolution PDF from template and data.

**Parameters:**
- `template_path` (str): Path to the LaTeX template file
- `data` (Dict[str, Any]): Data dictionary for template rendering
- `output_dir` (str): Directory where files should be generated
- `filename_base` (str): Base filename (without extension)

**Returns:**
- `PDFResult`: Generation result with PDF path and compilation details

**Example:**
```python
generator = PDFGenerator()
result = generator.generate_resolution(
    template_path="templates/resolution.tex",
    data={"title": "Monthly Budget", "month": "January"},
    output_dir="output",
    filename_base="resolution_jan"
)
if result.success:
    print(f"PDF created: {result.pdf_path}")
```

#### check_latex_availability

```python
check_latex_availability() -> bool
```

Check if pdflatex is available on the system.

**Returns:**
- `bool`: True if pdflatex is available, False otherwise

#### compile_to_pdf

```python
compile_to_pdf(tex_file: str, output_dir: str) -> CompilationResult
```

Compile LaTeX file to PDF using pdflatex.

**Parameters:**
- `tex_file` (str): Path to the .tex file to compile
- `output_dir` (str): Directory where PDF should be generated

**Returns:**
- `CompilationResult`: Compilation details including success status and logs

#### clean_temp_files

```python
clean_temp_files(base_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]
```

Clean temporary files generated during LaTeX compilation.

**Parameters:**
- `base_path` (str): Base path (without extension) of files to clean
- `extensions` (optional): List of extensions to clean. Defaults to ['.aux', '.log', '.fls', '.fdb_latexmk', '.synctex.gz']

**Returns:**
- `Dict[str, Any]`: Cleanup results including success count and errors

## LaTeXProcessor

The `LaTeXProcessor` class handles character escaping and template processing for safe LaTeX compilation.

### Methods

#### escape_special_characters

```python
escape_special_characters(text: str) -> str
```

Escape special characters in text to make it safe for LaTeX processing.

**Parameters:**
- `text` (str): Input text that may contain special characters

**Returns:**
- `str`: Text with all special characters properly escaped for LaTeX

**Example:**
```python
processor = LaTeXProcessor()
safe_text = processor.escape_special_characters("Cost: $1,500 & taxes")
# Result: "Cost: \\$1,500 \\& taxes"
```

#### process_description

```python
process_description(description: str) -> str
```

Process expense/investment descriptions for safe LaTeX inclusion.

**Parameters:**
- `description` (str): Raw description text from user input

**Returns:**
- `str`: LaTeX-safe description text

#### validate_escaped_text

```python
validate_escaped_text(text: str) -> bool
```

Validate that text has been properly escaped for LaTeX.

**Parameters:**
- `text` (str): Text to validate

**Returns:**
- `bool`: True if text appears to be properly escaped, False otherwise

### Character Escape Map

The processor uses the following escape mappings:

```python
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
```

## SystemChecker

The `SystemChecker` class validates system dependencies and configuration.

### Methods

#### check_all_dependencies

```python
check_all_dependencies() -> DependencyResult
```

Check all required system dependencies.

**Returns:**
- `DependencyResult`: Result containing missing dependencies and installation instructions

#### check_latex_installation

```python
check_latex_installation() -> Result
```

Check if pdflatex is available in the system.

**Returns:**
- `Result`: Success if pdflatex is available, failure otherwise

#### validate_configuration

```python
validate_configuration() -> ConfigurationResult
```

Validate all configuration files and directories, creating missing ones.

**Returns:**
- `ConfigurationResult`: Result containing validation status and created items

#### get_system_info

```python
get_system_info() -> Dict[str, str]
```

Get basic system information for troubleshooting.

**Returns:**
- `Dict[str, str]`: System information including platform, Python version, etc.

## Result Classes

### Result

Base result class for all operations.

```python
@dataclass
class Result:
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
```

### PDFResult

Result class for PDF generation operations.

```python
@dataclass
class PDFResult(Result):
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    compilation_log: Optional[str] = None
```

### AnalysisResult

Result class for financial analysis operations.

```python
@dataclass
class AnalysisResult(Result):
    total_expenses: float = 0.0
    expenses_by_category: Dict[str, float] = None
    total_investments: float = 0.0
    analysis_data: Optional[Dict[str, Any]] = None
```

### DependencyResult

Result class for dependency checking operations.

```python
@dataclass
class DependencyResult(Result):
    missing_dependencies: Optional[List[str]] = None
    installation_instructions: Optional[Dict[str, str]] = None
```

### ConfigurationResult

Result class for configuration validation operations.

```python
@dataclass
class ConfigurationResult(Result):
    missing_files: Optional[List[str]] = None
    missing_directories: Optional[List[str]] = None
    created_files: Optional[List[str]] = None
    created_directories: Optional[List[str]] = None
```

## Exception Classes

### PECOError

Base exception class for all PECO-related errors.

```python
class PECOError(Exception):
    def __init__(self, message: str, error_code: str = None, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
```

### LaTeXError

Exception for LaTeX-related errors.

```python
class LaTeXError(PECOError):
    pass
```

### DataError

Exception for data-related errors.

```python
class DataError(PECOError):
    pass
```

### ConfigurationError

Exception for configuration-related errors.

```python
class ConfigurationError(PECOError):
    pass
```

## Configuration

### Environment Configuration

Get configuration for specific environment:

```python
import config

# Get current environment configuration
env_config = config.get_config_for_environment()

# Get specific environment configuration
dev_config = config.get_config_for_environment('development')
```

### Configuration Validation

Validate current configuration:

```python
validation_result = config.validate_configuration()
print(f"Valid: {validation_result['valid']}")
print(f"Issues: {validation_result['issues']}")
print(f"Warnings: {validation_result['warnings']}")
```

### Directory Management

Create default directory structure:

```python
result = config.create_default_directories()
print(f"Created directories: {result['created_directories']}")
```

## Error Handling Patterns

All service methods follow consistent error handling patterns:

### Success Pattern

```python
result = service_method()
if result.success:
    # Handle success
    data = result.data
    print(result.message)
else:
    # Handle failure
    print(f"Error: {result.message}")
    if result.error_code:
        print(f"Error code: {result.error_code}")
```

### Exception Handling

```python
try:
    result = service_method()
except PECOError as e:
    print(f"PECO Error: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Usage Examples

### Complete Workflow Example

```python
from services.data_manager import DataManager
from services.pdf_generator import PDFGenerator
from services.system_checker import SystemChecker

# 1. Validate system
checker = SystemChecker()
system_result = checker.validate_complete_system()
if not system_result.success:
    print(f"System validation failed: {system_result.message}")
    exit(1)

# 2. Register expense
dm = DataManager()
expense_result = dm.register_expense(1500.0, "Comida", "Almuerzo")
if expense_result.success:
    print("Expense registered successfully")

# 3. Generate monthly analysis
analysis = dm.get_monthly_analysis(7, 2025)
if analysis.success:
    print(f"Total expenses: ${analysis.total_expenses}")

# 4. Generate PDF report
generator = PDFGenerator()
pdf_result = generator.generate_resolution(
    template_path="templates/monthly_report.tex",
    data=analysis.analysis_data,
    output_dir="reports",
    filename_base="monthly_report_july"
)
if pdf_result.success:
    print(f"PDF generated: {pdf_result.pdf_path}")
```

### Error Recovery Example

```python
from services.data_manager import DataManager
from services.exceptions import DataError

dm = DataManager()

# Validate data integrity first
integrity_result = dm.validate_data_integrity()
if not integrity_result.success:
    print(f"Data integrity issues: {integrity_result.message}")
    # Handle specific issues based on error_code
    if integrity_result.error_code == "FILE_NOT_FOUND":
        print("Recreating missing data files...")
        # Implement recovery logic

# Proceed with operations
try:
    result = dm.register_expense(amount, category, description)
    if not result.success:
        if result.error_code == "INVALID_AMOUNT":
            print("Please enter a valid amount")
        elif result.error_code == "MISSING_CATEGORY":
            print("Category is required")
except DataError as e:
    print(f"Data error: {e.message}")
    # Implement specific error handling
```