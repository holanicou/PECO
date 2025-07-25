# Design Document

## Overview

El diseño propuesto mejora la aplicación PECO mediante una arquitectura más modular, mejor manejo de errores, procesamiento robusto de caracteres especiales para LaTeX, y una interfaz web mejorada. La solución se enfoca en crear una base sólida que permita la expansión futura mientras resuelve los problemas actuales de interconexión y generación de PDFs.

## Architecture

### Current Architecture Issues
- Scripts Python independientes con comunicación limitada
- Manejo de errores inconsistente entre módulos
- Falta de validación de dependencias del sistema
- Procesamiento de caracteres especiales inexistente
- Interfaz web con feedback limitado

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Forms & UI    │  │  Error Display  │  │  Feedback   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
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

## Components and Interfaces

### 1. Core Service Layer

#### DataManager Class
```python
class DataManager:
    def register_expense(self, amount: float, category: str, description: str) -> Result
    def register_investment(self, asset: str, operation_type: str, amount: float) -> Result
    def get_monthly_analysis(self, month: int, year: int) -> AnalysisResult
    def validate_data_integrity(self) -> ValidationResult
```

#### PDFGenerator Class
```python
class PDFGenerator:
    def __init__(self, latex_processor: LaTeXProcessor)
    def generate_resolution(self, config: ResolutionConfig) -> PDFResult
    def check_latex_availability(self) -> bool
    def clean_temp_files(self, base_path: str) -> None
```

#### LaTeXProcessor Class
```python
class LaTeXProcessor:
    def escape_special_characters(self, text: str) -> str
    def process_template(self, template_path: str, data: dict) -> str
    def compile_to_pdf(self, tex_file: str, output_dir: str) -> CompilationResult
```

### 2. Character Escaping System

#### Special Characters Mapping
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
    '\\': r'\textbackslash{}'
}
```

### 3. Enhanced Web Interface

#### Improved Error Handling
- Real-time form validation
- Progressive feedback during long operations
- Detailed error messages with suggested solutions
- Connection status indicators

#### User Experience Improvements
- Loading states for all operations
- Success/error notifications
- Form auto-save functionality
- Better responsive design

## Data Models

### Result Classes
```python
@dataclass
class Result:
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None

@dataclass
class PDFResult(Result):
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    compilation_log: Optional[str] = None

@dataclass
class AnalysisResult(Result):
    total_expenses: float
    expenses_by_category: Dict[str, float]
    total_investments: float
    chart_path: Optional[str] = None
```

### Configuration Models
```python
@dataclass
class ResolutionConfig:
    title: str
    month_name: str
    previous_month: str
    previous_amount: float
    previous_expenses: List[ExpenseItem]
    additional_considerations: List[str]
    articles: List[str]
    
@dataclass
class ExpenseItem:
    description: str
    amount: float
```

## Error Handling

### Centralized Error Management
```python
class PECOError(Exception):
    def __init__(self, message: str, error_code: str, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class LaTeXError(PECOError):
    pass

class DataError(PECOError):
    pass

class ConfigurationError(PECOError):
    pass
```

### Error Recovery Strategies
1. **File Access Errors**: Automatic directory creation, permission checks
2. **LaTeX Compilation Errors**: Detailed error parsing, suggestion system
3. **Data Validation Errors**: Field-specific error messages, correction hints
4. **Configuration Errors**: Auto-generation of missing config files

## Testing Strategy

### Unit Testing
- Test each service class independently
- Mock external dependencies (file system, subprocess calls)
- Test character escaping with comprehensive special character sets
- Validate error handling paths

### Integration Testing
- Test complete workflows (expense registration → analysis → PDF generation)
- Test web interface with real backend calls
- Validate file operations with temporary directories
- Test LaTeX compilation with sample documents

### System Testing
- End-to-end user scenarios
- Performance testing with large datasets
- Cross-platform compatibility (Windows focus)
- LaTeX dependency validation

### Test Data Strategy
- Sample CSV/Excel files with various data scenarios
- Test configurations with special characters
- Mock LaTeX environments for testing without full LaTeX installation
- Error simulation for robust error handling testing

## Implementation Phases

### Phase 1: Core Infrastructure
1. Create service layer classes
2. Implement centralized error handling
3. Add character escaping system
4. Create comprehensive logging

### Phase 2: Data Management
1. Refactor existing scripts to use new service layer
2. Add data validation and integrity checks
3. Improve file handling with proper error recovery
4. Enhance configuration management

### Phase 3: PDF Generation
1. Implement robust LaTeX processing
2. Add dependency checking for pdflatex
3. Create comprehensive error reporting for compilation issues
4. Add automatic cleanup and file management

### Phase 4: Web Interface
1. Enhance UI with better error display
2. Add real-time feedback and loading states
3. Improve form validation and user experience
4. Add connection monitoring and retry logic

### Phase 5: Testing and Polish
1. Comprehensive testing suite
2. Performance optimization
3. Documentation updates
4. User acceptance testing