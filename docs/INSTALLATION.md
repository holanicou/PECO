# PECO Installation and Setup Guide

This guide provides step-by-step instructions for installing and setting up the PECO personal finance management system.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Verification](#verification)
- [First Run](#first-run)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Operating System
- Windows 10/11
- macOS 10.14 or later
- Linux (Ubuntu 18.04+ or equivalent)

### Software Requirements
- **Python 3.7 or higher** (Required)
- **LaTeX Distribution** (Required for PDF generation)
- **Git** (Optional, for version control)

### Hardware Requirements
- Minimum 2GB RAM
- 1GB free disk space
- Internet connection (for initial setup)

## Installation Steps

### Step 1: Install Python

#### Windows
1. Download Python from https://www.python.org/downloads/
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### macOS
1. **Using Homebrew** (Recommended):
   ```bash
   brew install python
   ```

2. **Using Official Installer**:
   - Download from https://www.python.org/downloads/
   - Run the installer

3. Verify installation:
   ```bash
   python3 --version
   pip3 --version
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Step 2: Install LaTeX Distribution

LaTeX is required for PDF generation functionality.

#### Windows - Install MiKTeX (Recommended)
1. Download MiKTeX from https://miktex.org/download
2. Run the installer as Administrator
3. Choose "Install for all users" if possible
4. Select "Yes" for automatic package installation
5. Verify installation:
   ```cmd
   pdflatex --version
   ```

#### Windows - Alternative: TeX Live
1. Download TeX Live from https://www.tug.org/texlive/
2. Run the installer (this may take a while)
3. Add TeX Live bin directory to PATH if not done automatically

#### macOS - Install MacTeX
1. **Using Homebrew**:
   ```bash
   brew install --cask mactex
   ```

2. **Using Official Installer**:
   - Download MacTeX from https://www.tug.org/mactex/
   - Run the installer (requires ~4GB disk space)

3. Verify installation:
   ```bash
   pdflatex --version
   ```

#### Linux - Install TeX Live
```bash
sudo apt update
sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

### Step 3: Download PECO

#### Option A: Download ZIP
1. Download the PECO source code as ZIP
2. Extract to your desired location
3. Navigate to the extracted directory

#### Option B: Clone with Git
```bash
git clone <repository-url>
cd peco
```

### Step 4: Set Up Python Environment

#### Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv peco_env
peco_env\Scripts\activate

# macOS/Linux
python3 -m venv peco_env
source peco_env/bin/activate
```

#### Install Python Dependencies
```bash
pip install flask pandas openpyxl jinja2 matplotlib
```

Or if you have a requirements.txt file:
```bash
pip install -r requirements.txt
```

### Step 5: Initial System Validation

Run the system checker to validate your installation:

```python
python -c "
from services.system_checker import SystemChecker
checker = SystemChecker()
result = checker.validate_complete_system()
print('System Status:', 'OK' if result.success else 'ISSUES FOUND')
print('Message:', result.message)
if not result.success and result.installation_instructions:
    print('Installation Instructions:')
    for dep, instruction in result.installation_instructions.items():
        print(f'  {dep}: {instruction}')
"
```

## Configuration

### Automatic Configuration

PECO will automatically create necessary directories and configuration files on first run. The system checker will:

1. Create required directories:
   - `03_Trackers/` - Data files
   - `06_Reportes/` - Generated reports
   - `01_Resoluciones/` - PDF resolutions
   - `logs/` - Application logs
   - `static/05_Templates_y_Recursos/` - Templates and resources

2. Create default configuration files:
   - `static/05_Templates_y_Recursos/config_mes.json` - Monthly configuration
   - `static/05_Templates_y_Recursos/presupuesto_base.json` - Budget configuration
   - `03_Trackers/gastos_mensuales.csv` - Expenses tracking
   - `03_Trackers/inversiones.xlsx` - Investments tracking

### Manual Configuration (Optional)

#### Environment Configuration
Set environment variable for different configurations:

```bash
# Windows
set PECO_ENV=development

# macOS/Linux
export PECO_ENV=development
```

Available environments:
- `production` (default) - Optimized for regular use
- `development` - Debug mode, verbose logging
- `testing` - Minimal logging, testing optimizations

#### Custom Configuration
Edit `config.py` to customize:

```python
# Logging level
LOGGING_CONFIG["level"] = "DEBUG"  # or INFO, WARNING, ERROR

# PDF generation timeout
PDF_CONFIG["latex_timeout"] = 120  # seconds

# Web server port
WEB_CONFIG["port"] = 5001  # if 5000 is in use
```

### Template Setup

#### Required Template Files
Place these files in `static/05_Templates_y_Recursos/`:

1. **plantilla_resolucion.tex** - LaTeX template for resolutions
2. **logo.png** - Organization logo (optional)
3. **firma.png** - Signature image (optional)

#### Sample Template
If you don't have a template, PECO will create a basic one automatically.

## Verification

### Test System Components

#### 1. Test Python Dependencies
```python
python -c "
import flask, pandas, openpyxl, jinja2, matplotlib
print('All Python dependencies installed successfully')
"
```

#### 2. Test LaTeX Installation
```python
python -c "
from services.pdf_generator import PDFGenerator
generator = PDFGenerator()
if generator.check_latex_availability():
    print('LaTeX is properly installed')
else:
    print('LaTeX installation issue - check TROUBLESHOOTING.md')
"
```

#### 3. Test Data Management
```python
python -c "
from services.data_manager import DataManager
dm = DataManager()
result = dm.validate_data_integrity()
print('Data integrity:', 'OK' if result.success else result.message)
"
```

#### 4. Test Configuration
```python
python -c "
import config
validation = config.validate_configuration()
print('Configuration:', 'OK' if validation['valid'] else 'Issues found')
if validation['issues']:
    print('Issues:', validation['issues'])
"
```

## First Run

### Start the Web Application

```bash
python app.py
```

You should see output similar to:
```
INFO - peco.main - Logging initialized - Level: INFO
INFO - peco.system_checker - All system dependencies are available
INFO - peco.main - PECO application starting...
 * Running on http://127.0.0.1:5000
```

### Access the Web Interface

1. Open your web browser
2. Navigate to http://127.0.0.1:5000
3. You should see the PECO web interface

### Test Basic Functionality

#### Register a Test Expense
1. Use the web interface or run:
   ```bash
   python registrar_gasto.py
   ```
2. Enter test data when prompted

#### Generate a Test Report
```bash
python analisis_mensual.py
```

#### Generate a Test PDF
```bash
python generar_resolucion.py
```

## Troubleshooting

### Common Installation Issues

#### Python Not Found
- **Windows**: Ensure Python is added to PATH during installation
- **macOS**: Use `python3` instead of `python`
- **Linux**: Install python3-dev if compilation errors occur

#### LaTeX Not Found
- Restart terminal/command prompt after LaTeX installation
- Check if LaTeX bin directory is in PATH
- Try running `pdflatex --version` manually

#### Permission Errors
- **Windows**: Run command prompt as Administrator
- **macOS/Linux**: Check file permissions with `ls -la`
- Ensure write permissions for application directory

#### Port Already in Use
```bash
# Change port in config.py
WEB_CONFIG["port"] = 5001

# Or kill existing process
# Windows
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# macOS/Linux
lsof -ti:5000 | xargs kill -9
```

### Getting Help

#### Check System Status
```python
python -c "
from services.system_checker import SystemChecker
checker = SystemChecker()
info = checker.get_system_info()
print('System Info:')
for key, value in info.items():
    print(f'  {key}: {value}')
"
```

#### Check Logs
```bash
# View recent logs
tail -f logs/peco_*.log

# Search for errors
grep -i error logs/peco_*.log
```

#### Validate Complete Setup
```python
python -c "
from services.system_checker import SystemChecker
import config

print('=== PECO Installation Validation ===')
checker = SystemChecker()
result = checker.validate_complete_system()
print(f'Overall Status: {\"PASS\" if result.success else \"FAIL\"}')
print(f'Message: {result.message}')

config_result = config.validate_configuration()
print(f'Configuration: {\"PASS\" if config_result[\"valid\"] else \"FAIL\"}')
if config_result['issues']:
    print('Issues found:')
    for issue in config_result['issues']:
        print(f'  - {issue}')
"
```

### Next Steps

After successful installation:

1. **Customize Templates**: Edit LaTeX templates in `static/05_Templates_y_Recursos/`
2. **Configure Budget**: Edit `presupuesto_base.json` with your budget categories
3. **Set Up Backup**: Consider backing up the `03_Trackers/` directory regularly
4. **Explore Features**: Try all the scripts and web interface features

For detailed usage instructions, see the main [README.md](README.md) file.
For troubleshooting specific issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
For API documentation, see [API.md](API.md).