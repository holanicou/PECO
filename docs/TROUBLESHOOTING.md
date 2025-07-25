# PECO Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the PECO financial management system.

## Table of Contents

- [System Requirements Issues](#system-requirements-issues)
- [LaTeX and PDF Generation Issues](#latex-and-pdf-generation-issues)
- [Data File Issues](#data-file-issues)
- [Configuration Issues](#configuration-issues)
- [Web Interface Issues](#web-interface-issues)
- [Character Encoding Issues](#character-encoding-issues)
- [Performance Issues](#performance-issues)

## System Requirements Issues

### Problem: "pdflatex is not available" Error

**Symptoms:**
- Error message: "pdflatex is not available. Please install a LaTeX distribution."
- PDF generation fails

**Solutions:**

#### Windows
1. **Install MiKTeX** (Recommended):
   - Download from https://miktex.org/download
   - Run the installer with administrator privileges
   - Choose "Install for all users" if possible
   - After installation, restart your command prompt/terminal

2. **Install TeX Live**:
   - Download from https://www.tug.org/texlive/
   - Follow the installation instructions
   - Add the TeX Live bin directory to your PATH

3. **Verify Installation**:
   ```bash
   pdflatex --version
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

#### macOS
1. **Install MacTeX**:
   - Download from https://www.tug.org/mactex/
   - Run the installer

2. **Using Homebrew**:
   ```bash
   brew install --cask mactex
   ```

### Problem: Python Version Too Old

**Symptoms:**
- Error: "Python version X.X.X is too old. Minimum required: 3.7"

**Solution:**
1. Install Python 3.7 or newer from https://www.python.org/downloads/
2. Update your virtual environment if using one
3. Verify installation: `python --version`

### Problem: Missing Python Dependencies

**Symptoms:**
- ImportError or ModuleNotFoundError for packages like pandas, flask, etc.

**Solution:**
```bash
pip install flask pandas openpyxl jinja2 matplotlib
```

## LaTeX and PDF Generation Issues

### Problem: LaTeX Compilation Errors

**Symptoms:**
- PDF generation fails with LaTeX errors
- Error messages about missing packages or syntax errors

**Diagnostic Steps:**
1. Check the LaTeX log file in the output directory
2. Look for specific error messages in the compilation output

**Common Solutions:**

#### Missing LaTeX Packages
```bash
# For MiKTeX (Windows)
miktex-console  # Open MiKTeX Console and install missing packages

# For TeX Live (Linux/macOS)
tlmgr install <package-name>
```

#### Character Encoding Issues in LaTeX
- The system automatically escapes special characters
- If you see unescaped characters in the LaTeX file, check the LaTeXProcessor

#### Template File Issues
1. Verify template file exists: `static/05_Templates_y_Recursos/plantilla_resolucion.tex`
2. Check template syntax for Jinja2 compatibility
3. Ensure template uses UTF-8 encoding

### Problem: PDF Generation Timeout

**Symptoms:**
- Error: "LaTeX compilation timed out after 60 seconds"

**Solutions:**
1. Increase timeout in configuration:
   ```python
   PDF_CONFIG["latex_timeout"] = 120  # 2 minutes
   ```
2. Check for infinite loops in LaTeX template
3. Simplify complex LaTeX expressions

### Problem: Resource Files Not Found

**Symptoms:**
- LaTeX errors about missing logo.png or firma.png
- PDF generates but images are missing

**Solutions:**
1. Ensure files exist in `static/05_Templates_y_Recursos/`:
   - `logo.png`
   - `firma.png`
2. Check file permissions (readable by the application)
3. Verify image file formats are supported

## Data File Issues

### Problem: CSV File Corruption

**Symptoms:**
- Error reading expense data
- Malformed CSV structure

**Solutions:**
1. **Backup and Recreate**:
   ```bash
   cp 03_Trackers/gastos_mensuales.csv 03_Trackers/gastos_mensuales.csv.backup
   ```
2. **Validate CSV Structure**:
   - Required columns: `Fecha,Categoria,Descripcion,Monto_ARS`
   - Ensure UTF-8 encoding
   - Check for unescaped commas in data

3. **Use Data Validation**:
   ```python
   from services.data_manager import DataManager
   dm = DataManager()
   result = dm.validate_data_integrity()
   print(result.message)
   ```

### Problem: Excel File Issues

**Symptoms:**
- Cannot read investment data
- Excel file corruption errors

**Solutions:**
1. **Recreate Excel File**:
   ```python
   import pandas as pd
   df = pd.DataFrame(columns=['Fecha', 'Activo', 'Tipo', 'Monto_ARS'])
   df.to_excel('03_Trackers/inversiones.xlsx', index=False)
   ```

2. **Check File Permissions**:
   - Ensure the file is not open in Excel
   - Verify write permissions to the directory

### Problem: JSON Configuration Errors

**Symptoms:**
- JSON decode errors
- Configuration file not found

**Solutions:**
1. **Validate JSON Syntax**:
   ```python
   import json
   with open('static/05_Templates_y_Recursos/config_mes.json', 'r') as f:
       data = json.load(f)  # Will raise error if invalid
   ```

2. **Recreate Configuration Files**:
   ```python
   from services.system_checker import SystemChecker
   checker = SystemChecker()
   result = checker.validate_configuration()
   ```

## Configuration Issues

### Problem: Missing Directories

**Symptoms:**
- FileNotFoundError when accessing data files
- Permission denied errors

**Solutions:**
1. **Auto-create Directories**:
   ```python
   import config
   result = config.create_default_directories()
   print(result)
   ```

2. **Manual Directory Creation**:
   ```bash
   mkdir -p 03_Trackers 06_Reportes 01_Resoluciones logs
   mkdir -p static/05_Templates_y_Recursos
   ```

### Problem: Permission Errors

**Symptoms:**
- "Permission denied" when writing files
- Cannot create directories

**Solutions:**
1. **Check Directory Permissions**:
   ```bash
   ls -la  # Check permissions
   chmod 755 03_Trackers 06_Reportes 01_Resoluciones  # Fix permissions
   ```

2. **Run with Appropriate Privileges**:
   - On Windows: Run command prompt as Administrator
   - On Linux/macOS: Use `sudo` if necessary (not recommended for regular use)

## Web Interface Issues

### Problem: Flask Application Won't Start

**Symptoms:**
- Port already in use errors
- Flask import errors

**Solutions:**
1. **Change Port**:
   ```python
   # In config.py
   WEB_CONFIG["port"] = 5001  # Use different port
   ```

2. **Kill Existing Process**:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <process_id> /F
   
   # Linux/macOS
   lsof -ti:5000 | xargs kill -9
   ```

### Problem: AJAX Requests Failing

**Symptoms:**
- Forms don't submit properly
- No response from server

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify Flask routes are properly defined
3. Check CORS settings if accessing from different domain

## Character Encoding Issues

### Problem: Special Characters in LaTeX

**Symptoms:**
- LaTeX compilation errors with special characters
- Garbled text in PDF output

**Solutions:**
1. **Automatic Escaping** (should work automatically):
   ```python
   from services.latex_processor import LaTeXProcessor
   processor = LaTeXProcessor()
   safe_text = processor.escape_special_characters("$1,500 & taxes")
   ```

2. **Manual Character Checking**:
   ```python
   # Check if text is properly escaped
   result = processor.validate_escaped_text(your_text)
   ```

### Problem: UTF-8 Encoding Issues

**Symptoms:**
- UnicodeDecodeError when reading files
- Accented characters display incorrectly

**Solutions:**
1. **Ensure UTF-8 Encoding**:
   - Save all text files with UTF-8 encoding
   - Check your text editor's encoding settings

2. **Force UTF-8 in Python**:
   ```python
   with open(filename, 'r', encoding='utf-8') as f:
       content = f.read()
   ```

## Performance Issues

### Problem: Slow PDF Generation

**Symptoms:**
- PDF generation takes very long
- Application appears to hang

**Solutions:**
1. **Check LaTeX Installation**:
   - Ensure LaTeX packages are properly installed
   - Update MiKTeX/TeX Live to latest version

2. **Optimize Templates**:
   - Remove unnecessary LaTeX packages
   - Simplify complex formatting

3. **Monitor System Resources**:
   - Check CPU and memory usage during compilation
   - Close unnecessary applications

### Problem: Large Log Files

**Symptoms:**
- Disk space issues
- Slow application startup

**Solutions:**
1. **Configure Log Rotation**:
   ```python
   # In config.py
   LOGGING_CONFIG["max_file_size"] = 5 * 1024 * 1024  # 5MB
   LOGGING_CONFIG["backup_count"] = 3
   ```

2. **Clean Old Logs**:
   ```bash
   # Remove logs older than 30 days
   find logs/ -name "*.log*" -mtime +30 -delete
   ```

## Getting Help

### System Information for Support

When reporting issues, include this information:

```python
from services.system_checker import SystemChecker
import config

checker = SystemChecker()
system_info = checker.get_system_info()
config_validation = config.validate_configuration()

print("System Info:", system_info)
print("Config Validation:", config_validation)
```

### Log Analysis

Check the application logs for detailed error information:

```bash
# View recent logs
tail -f logs/peco_*.log

# Search for errors
grep -i error logs/peco_*.log
```

### Common Error Patterns

1. **File Not Found**: Usually indicates missing configuration or data files
2. **Permission Denied**: Check file/directory permissions
3. **LaTeX Errors**: Check LaTeX installation and template syntax
4. **Import Errors**: Missing Python dependencies
5. **JSON Errors**: Invalid configuration file syntax

### Emergency Recovery

If the system is completely broken:

1. **Backup Data**:
   ```bash
   cp -r 03_Trackers 03_Trackers_backup
   ```

2. **Reset Configuration**:
   ```python
   from services.system_checker import SystemChecker
   checker = SystemChecker()
   checker.validate_configuration()  # Recreates missing files
   ```

3. **Reinstall Dependencies**:
   ```bash
   pip install --force-reinstall flask pandas openpyxl jinja2 matplotlib
   ```

For additional help, check the logs directory for detailed error messages and stack traces.