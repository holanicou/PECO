# PECO Project Structure

## Overview
This document describes the final, optimized structure of the PECO (Personal Economy Control) project after cleanup and reorganization.

## Core Application Files
- `PECO.py` - Main CLI entry point with unified command interface
- `app.py` - Flask web application server
- `config.py` - Application configuration settings
- `peco.db` - SQLite database file

## Core Modules
- `analisis_mensual.py` - Monthly analysis functionality
- `generar_resolucion.py` - PDF resolution generation
- `migrate_to_sqlite.py` - Database migration utilities
- `run_unit_tests.py` - Test runner script

## Services Layer (`services/`)
- `base.py` - Base service classes
- `config_validator.py` - Configuration validation service
- `database.py` - Database connection management
- `data_manager.py` - Centralized data access layer
- `exceptions.py` - Custom exception classes
- `latex_processor.py` - LaTeX template processing
- `logging_config.py` - Logging configuration
- `pdf_generator.py` - PDF generation service
- `system_checker.py` - System dependency validation

## Frontend (`static/`)
- `index_modular.html` - Main web interface
- `css/` - Stylesheets
- `js/` - JavaScript modules including forms.js
- `05_Templates_y_Recursos/` - LaTeX templates and resources

## Data Directories
- `01_Resoluciones/` - Generated resolution PDFs
- `02_Comprobantes/` - Supporting documents
- `03_Trackers/` - CSV and Excel data files
- `04_Planificación/` - Planning documents
- `06_Reportes/` - Generated reports

## Documentation (`docs/`)
- `API.md` - API documentation
- `INSTALLATION.md` - Installation guide
- `README.md` - Project overview
- `SERVICE_LAYER.md` - Service layer documentation
- `TROUBLESHOOTING.md` - Troubleshooting guide

## Testing
- `test_*.py` - Comprehensive test suite covering all modules
- Unit tests, integration tests, and service layer tests

## Configuration & Dependencies
- `requirements.txt` - Python dependencies with exact versions
- `.kiro/` - Kiro IDE configuration and specs
- `logs/` - Application log files
- `output/` - Generated output files

## Key Features
1. **Unified CLI Interface**: All commands accessible through `python PECO.py`
2. **Centralized Data Access**: All database operations through DataManager
3. **Service Layer Architecture**: Clean separation of concerns
4. **Comprehensive Testing**: Full test coverage for all components
5. **Dynamic Form Generation**: JavaScript-based form management
6. **Intelligent LaTeX Templates**: Jinja2-powered PDF generation
7. **Configuration Validation**: Robust validation and error handling

## Usage
- **CLI**: `python PECO.py [registrar|invertir|generar|analizar] [options]`
- **Web Interface**: `python app.py` then visit http://localhost:5000
- **Tests**: `python run_unit_tests.py`