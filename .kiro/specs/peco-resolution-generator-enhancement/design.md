# Design Document

## Overview

The PECO Resolution Generator Enhancement transforms the existing basic PDF generation system into a sophisticated, user-friendly, and maintainable solution. The design follows a three-layer approach: standardized data structure, dynamic user interface, and intelligent template processing, complemented by comprehensive project optimization.

## Architecture

### Data Layer
- **Standardized JSON Configuration**: Central config_mes.json with structured schema
- **SQLite Database**: Centralized through DataManager for all data operations
- **File System**: Organized static resources and templates

### Presentation Layer
- **Dynamic Forms**: JavaScript-based form generation with real-time manipulation
- **Responsive UI**: Tailwind CSS-styled interface with intuitive controls
- **Modal System**: Structured form presentation within existing modal framework

### Processing Layer
- **LaTeX Template Engine**: Jinja2-powered dynamic template rendering
- **PDF Generation**: Enhanced LaTeX processing with automatic calculations
- **CLI Interface**: Unified command-line interface through main PECO.py

### Service Layer
- **DataManager**: Centralized database access and data validation
- **FormManager**: Client-side form state management and data collection
- **Template Processor**: Server-side template rendering and PDF generation

## Components and Interfaces

### 1. Data Structure Component

**config_mes.json Schema:**
```json
{
  "mes_iso": "YYYY-MM",
  "titulo_base": "string",
  "visto": "string",
  "considerandos": [
    {
      "tipo": "gasto_anterior|texto",
      "descripcion": "string", // for gasto_anterior
      "monto": "string",       // for gasto_anterior
      "contenido": "string"    // for texto
    }
  ],
  "articulos": ["string"],
  "anexo": {
    "titulo": "string",
    "items": [
      {
        "categoria": "string",
        "monto": "string"
      }
    ],
    "penalizaciones": [
      {
        "categoria": "string",
        "monto": "string" // negative values
      }
    ],
    "nota_final": "string"
  }
}
```

**Interface Methods:**
- `loadConfig()`: Load and validate configuration
- `saveConfig(config)`: Save configuration with validation
- `calculateTotals(anexo)`: Compute subtotals and final amounts

### 2. Dynamic Form Component

**FormManager Class Extensions:**
```javascript
class FormManager {
  generateResolutionForm(config)     // Generate structured form HTML
  addListItem(containerId, key)      // Add dynamic list items
  addAnexoItem(containerId, key)     // Add anexo items with validation
  removeListItem(button)             // Remove dynamic items
  handleSaveAndGenerate()            // Collect and process form data
  validateFormData(data)             // Client-side validation
}
```

**Form Sections:**
1. **General Data**: Month selector, title input
2. **VISTO Section**: Multi-line text area
3. **CONSIDERANDO Section**: Dynamic list with add/remove functionality
4. **ARTICULOS Section**: Dynamic list for resolution articles
5. **ANEXO Section**: Structured items with category/amount pairs

### 3. Template Processing Component

**Enhanced LaTeX Template Features:**
- **Dynamic Considerandos**: Conditional rendering based on type
- **Auto-numbered Articles**: Automatic article numbering with proper formatting
- **Conditional Anexo**: Only renders if items exist
- **Automatic Calculations**: Server-side total computation
- **Responsive Layout**: Proper spacing and page breaks

**Template Variables:**
```latex
{{ fecha_larga }}           // Formatted date
{{ codigo_res }}            // Resolution code
{{ titulo_documento }}      // Document title
{{ visto }}                 // VISTO content
{{ considerandos }}         // Array of considerando objects
{{ articulos }}             // Array of article strings
{{ anexo }}                 // Anexo object with items and calculations
{{ mes_nombre }}            // Month name in Spanish
{{ anio }}                  // Year
```

### 4. CLI Unification Component

**Unified PECO.py Structure:**
```python
def main():
    parser = argparse.ArgumentParser(prog="peco")
    subparsers = parser.add_subparsers(dest="comando", required=True)
    
    # Command definitions
    parser_registrar = subparsers.add_parser("registrar")
    parser_invertir = subparsers.add_parser("invertir")
    parser_generar = subparsers.add_parser("generar")
    parser_analizar = subparsers.add_parser("analizar")
    
    # Direct function calls (no subprocess)
    if args.comando == "registrar":
        registrar_gasto_main(args.monto, args.categoria, args.desc)
    # ... other commands
```

## Data Models

### Configuration Model
```python
@dataclass
class ResolutionConfig:
    mes_iso: str
    titulo_base: str
    visto: str
    considerandos: List[Considerando]
    articulos: List[str]
    anexo: Anexo

@dataclass
class Considerando:
    tipo: str  # "gasto_anterior" or "texto"
    descripcion: Optional[str] = None
    monto: Optional[str] = None
    contenido: Optional[str] = None

@dataclass
class Anexo:
    titulo: str
    items: List[AnexoItem]
    penalizaciones: List[AnexoItem]
    nota_final: str
    subtotal: Optional[float] = None
    total_solicitado: Optional[float] = None
```

### Form Data Model
```javascript
const FormData = {
  mes_iso: string,
  titulo_base: string,
  visto: string,
  considerandos: Array<{tipo: string, contenido: string}>,
  articulos: Array<string>,
  anexo: {
    titulo: string,
    items: Array<{categoria: string, monto: string}>,
    penalizaciones: Array<{categoria: string, monto: string}>,
    nota_final: string
  }
}
```

## Error Handling

### Client-Side Validation
- **Form Validation**: Required fields, numeric validation for amounts
- **Real-time Feedback**: Immediate validation feedback on form inputs
- **Data Consistency**: Ensure all dynamic items have valid data before submission

### Server-Side Validation
- **JSON Schema Validation**: Validate configuration structure
- **Data Type Validation**: Ensure proper data types for all fields
- **Business Logic Validation**: Validate amounts, dates, and required fields

### Error Recovery
- **Graceful Degradation**: Fall back to basic functionality if advanced features fail
- **User Feedback**: Clear error messages with actionable guidance
- **Logging**: Comprehensive error logging for debugging

## Testing Strategy

### Unit Tests
- **Data Model Tests**: Validate configuration loading, saving, and calculations
- **Form Manager Tests**: Test dynamic form generation and data collection
- **Template Processing Tests**: Verify LaTeX template rendering with various data

### Integration Tests
- **End-to-End Form Flow**: Test complete form submission and PDF generation
- **CLI Integration**: Test unified CLI commands and their interactions
- **Database Integration**: Test DataManager centralization and data consistency

### User Acceptance Tests
- **Form Usability**: Test dynamic form manipulation and user experience
- **PDF Quality**: Verify generated PDF formatting and content accuracy
- **Performance**: Test system responsiveness with various data sizes

### Migration Tests
- **Data Migration**: Test conversion from old to new configuration format
- **Backward Compatibility**: Ensure existing functionality remains intact
- **File Cleanup**: Verify safe removal of redundant files

## Implementation Phases

### Phase 1: Data Structure Standardization
1. Update config_mes.json with new schema
2. Implement configuration validation
3. Add automatic calculation functions

### Phase 2: Dynamic Form Interface
1. Enhance FormManager with new methods
2. Implement dynamic list management
3. Add client-side validation

### Phase 3: Intelligent Template Processing
1. Update LaTeX template with Jinja2 features
2. Implement conditional rendering
3. Add automatic calculations

### Phase 4: Project Optimization
1. Unify CLI interface in PECO.py
2. Centralize database access in DataManager
3. Clean up redundant files
4. Generate requirements.txt

### Phase 5: Testing and Validation
1. Comprehensive testing of all components
2. User acceptance testing
3. Performance optimization
4. Documentation updates