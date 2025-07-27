# Requirements Document

## Introduction

This feature enhances the PECO project's resolution generator system by transforming it from a basic PDF generator into a powerful, structured, and user-friendly system. The enhancement includes standardizing the data structure, redesigning the user interface with dynamic forms, making the LaTeX template intelligent and flexible, and optimizing the overall project organization for better maintainability and efficiency.

## Requirements

### Requirement 1

**User Story:** As a PECO user, I want a standardized and structured data format for resolution configurations, so that I can easily manage and modify resolution data programmatically and through the interface.

#### Acceptance Criteria

1. WHEN the system loads resolution configuration THEN it SHALL use a standardized JSON structure with mes_iso, titulo_base, visto, considerandos, articulos, and anexo fields
2. WHEN processing dates THEN the system SHALL use ISO format (YYYY-MM) for easy date manipulation and automatic month name generation
3. WHEN handling considerandos and articulos THEN the system SHALL support both structured objects and simple text entries
4. WHEN managing anexo data THEN the system SHALL provide structured objects for items, penalizaciones, and calculations

### Requirement 2

**User Story:** As a PECO user, I want a dynamic and intuitive form interface for creating resolutions, so that I can easily add, remove, and modify resolution components without manual JSON editing.

#### Acceptance Criteria

1. WHEN opening the resolution form THEN the system SHALL display structured sections for general data, visto, considerandos, articulos, and anexo
2. WHEN working with considerandos and articulos THEN the user SHALL be able to dynamically add and remove items using buttons
3. WHEN managing anexo items THEN the user SHALL have separate input fields for categoria and monto with validation
4. WHEN saving the form THEN the system SHALL collect all dynamic form data and structure it properly for processing
5. WHEN the form loads existing data THEN it SHALL populate all fields correctly including dynamic lists

### Requirement 3

**User Story:** As a PECO user, I want an intelligent LaTeX template that adapts to different data structures, so that my generated PDFs are consistent and professional regardless of the content variations.

#### Acceptance Criteria

1. WHEN generating PDFs THEN the template SHALL dynamically render considerandos based on their type (gasto_anterior vs texto)
2. WHEN processing articulos THEN the template SHALL automatically number them and format them properly
3. WHEN including anexo data THEN the template SHALL only show the anexo page if items exist
4. WHEN calculating totals THEN the template SHALL automatically compute subtotals and final amounts
5. WHEN handling penalizaciones THEN the template SHALL include them in the anexo table with proper formatting

### Requirement 4

**User Story:** As a PECO developer/maintainer, I want a unified and optimized CLI system, so that I can manage all PECO operations from a single entry point without redundant code.

#### Acceptance Criteria

1. WHEN running CLI commands THEN all operations SHALL be accessible through the main PECO.py script
2. WHEN executing registrar, invertir, generar, or analizar commands THEN the system SHALL call the appropriate functions directly without subprocess overhead
3. WHEN managing the codebase THEN redundant script files SHALL be safely removed after functionality is consolidated
4. WHEN setting up the project THEN a requirements.txt file SHALL list all Python dependencies with exact versions

### Requirement 5

**User Story:** As a PECO developer/maintainer, I want centralized database access through DataManager, so that all database operations are secure, organized, and easy to debug.

#### Acceptance Criteria

1. WHEN accessing the database THEN all SQL queries SHALL be contained within the DataManager class
2. WHEN app.py or CLI scripts need data THEN they SHALL only call DataManager methods
3. WHEN debugging database issues THEN there SHALL be a single point of entry for all database operations
4. WHEN adding new database functionality THEN it SHALL be implemented as new DataManager methods

### Requirement 6

**User Story:** As a PECO user, I want automatic calculation and validation of resolution amounts, so that my financial data is accurate and consistent.

#### Acceptance Criteria

1. WHEN entering anexo items THEN the system SHALL validate that monto fields contain valid numbers
2. WHEN generating the PDF THEN the system SHALL automatically calculate subtotals and final amounts
3. WHEN including penalizaciones THEN they SHALL be properly subtracted from the total
4. WHEN displaying amounts THEN they SHALL be formatted consistently with proper currency symbols