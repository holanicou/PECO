# PECO - Personal Finance Management System

## Overview

PECO is a comprehensive personal finance management system that helps track expenses, investments, and generate financial reports and resolutions. The system has been enhanced with a robust service layer architecture, improved error handling, and comprehensive PDF generation capabilities.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Service Layer Documentation](#service-layer-documentation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Installation

### Prerequisites

1. **Python 3.7+**: Required for running the application
2. **LaTeX Distribution**: Required for PDF generation
   - **Windows**: Install [MiKTeX](https://miktex.org/download) or [TeX Live](https://www.tug.org/texlive/)
   - **Linux**: `sudo apt-get install texlive-latex-base texlive-latex-extra`
   - **macOS**: Install [MacTeX](https://www.tug.org/mactex/) or use Homebrew: `brew install --cask mactex`

### Python Dependencies

Install required Python packages:

```bash
pip install flask pandas openpyxl jinja2 matplotlib
```

### System Validation

The application includes automatic system validation. Run the following to check your setup:

```python
from services.system_checker import SystemChecker

checker = SystemChecker()
result = checker.validate_complete_system()
print(result.message)
```

## Quick Start

1. **Start the web application**:
   ```bash
   python app.py
   ```

2. **Register an expense**:
   ```bash
   python registrar_gasto.py
   ```

3. **Register an investment**:
   ```bash
   python registrar_inversion.py
   ```

4. **Generate monthly analysis**:
   ```bash
   python analisis_mensual.py
   ```

5. **Generate a resolution PDF**:
   ```bash
   python generar_resolucion.py
   ```

## Architecture

The PECO system follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Service Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Data Manager   │  │  PDF Generator  │  │ Validator   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   CSV Handler   │  │  Excel Handler  │  │ JSON Config │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **DataManager**: Handles expense and investment data operations
- **PDFGenerator**: Manages LaTeX compilation and PDF generation
- **LaTeXProcessor**: Handles character escaping and template processing
- **SystemChecker**: Validates system dependencies and configuration

## Service Layer Documentation

### DataManager

The `DataManager` class provides centralized data management for expenses and investments.

**Key Methods:**
- `register_expense(amount, category, description)`: Register a new expense
- `register_investment(asset, operation_type, amount)`: Register an investment
- `get_monthly_analysis(month, year)`: Get comprehensive monthly analysis
- `validate_data_integrity()`: Validate all data files

**Example Usage:**
```python
from services.data_manager import DataManager

dm = DataManager()
result = dm.register_expense(1500.0, "Comida", "Almuerzo en restaurante")
if result.success:
    print("Expense registered successfully")
else:
    print(f"Error: {result.message}")
```

### PDFGenerator

The `PDFGenerator` class handles LaTeX compilation and PDF generation with comprehensive error handling.

**Key Methods:**
- `generate_resolution(template_path, data, output_dir, filename_base)`: Generate PDF from template
- `check_latex_availability()`: Verify LaTeX installation
- `clean_temp_files(base_path)`: Clean temporary compilation files

**Example Usage:**
```python
from services.pdf_generator import PDFGenerator

generator = PDFGenerator()
result = generator.generate_resolution(
    template_path="templates/resolution.tex",
    data={"title": "Monthly Budget", "month": "January"},
    output_dir="output",
    filename_base="resolution_jan"
)
```

### LaTeXProcessor

The `LaTeXProcessor` class handles character escaping for safe LaTeX compilation.

**Key Methods:**
- `escape_special_characters(text)`: Escape problematic characters
- `process_description(description)`: Process expense descriptions safely

**Example Usage:**
```python
from services.latex_processor import LaTeXProcessor

processor = LaTeXProcessor()
safe_text = processor.escape_special_characters("Cost: $1,500 & taxes")
# Result: "Cost: \\$1,500 \\& taxes"
```

## Configuration

The system uses a comprehensive configuration system in `config.py`. Key configuration sections:

### Service Configuration

```python
# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# PDF Generation Configuration
PDF_CONFIG = {
    "latex_timeout": 60,
    "auto_cleanup": True,
    "compilation_retries": 1
}
```

### Environment-Specific Settings

Use environment variables to control behavior:

```bash
export PECO_ENV=development  # or testing, production
```

### Configuration Validation

Validate your configuration:

```python
import config
validation_result = config.validate_configuration()
print(validation_result)
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

## API Reference

See [API.md](API.md) for complete API documentation.

## Contributing

1. Follow the existing code style and architecture
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure all services follow the Result pattern for error handling

## License

This project is for personal use and educational purposes.