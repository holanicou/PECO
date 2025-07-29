# Implementation Plan

- [x] 1. Standardize data structure and configuration

  - Update config_mes.json with new standardized schema including mes_iso, structured considerandos, articulos arrays, and anexo object
  - Implement configuration validation functions to ensure data integrity
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

-

- [x] 2. Enhance FormManager with dynamic form generation

- [x] 2.1 Implement generateResolutionForm method with structured sections

  - Replace existing form generation with new structured approach that creates sections for general data, visto, considerandos, articulos, and anexo
  - Add helper functions createListItems and createAnexoItems for dynamic content generation
  - _Requirements: 2.1, 2.5_

- [x] 2.2 Add dynamic list management methods

  - Implement addListItem, addAnexoItem, and removeListItem methods for real-time form manipulation
  - Add proper event handling and DOM manipulation for dynamic form elements
  - _Requirements: 2.2, 2.3_

- [x] 2.3 Update handleSaveAndGenerate method for new data structure

  - Modify form data collection to work with new structured format
  - Implement client-side validation for form data before submission
  - _Requirements: 2.4, 6.1_

- [x] 3. Create intelligent LaTeX template with dynamic rendering

- [x] 3.1 Update plantilla_resolucion.tex with Jinja2 template features

  - Replace static template with dynamic Jinja2 template that handles variable content
  - Implement conditional rendering for different considerando types (gasto_anterior vs texto)
  - _Requirements: 3.1, 3.2_

- [x] 3.2 Add automatic calculations and conditional anexo rendering

  - Implement automatic total calculations for anexo items and penalizaciones
  - Add conditional anexo page rendering that only shows when items exist
  - _Requirements: 3.3, 3.4, 3.5, 6.2, 6.3, 6.4_

- [x] 4. Implement server-side configuration processing

- [x] 4.1 Create configuration validation and calculation functions

  - Add server-side validation for the new JSON schema
  - Implement automatic calculation functions for subtotals and final amounts
  - _Requirements: 1.1, 6.2, 6.3_

- [x] 4.2 Update PDF generation to work with new data structure

  - Modify existing PDF generation code to use new configuration format
  - Ensure proper data passing between form submission and template processing
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Unify CLI interface in main PECO.py

- [x] 5.1 Consolidate all CLI commands into single entry point

  - Replace subprocess calls with direct function imports and calls
  - Implement proper argument parsing for all existing commands (registrar, invertir, generar, analizar)
  - _Requirements: 4.1, 4.2_

- [x] 5.2 Update existing scripts to support direct function calls

  - Ensure registrar_gasto.py and registrar_inversion.py main functions can be called directly
  - Maintain backward compatibility while enabling direct imports
  - _Requirements: 4.1, 4.2_

- [x] 6. Centralize database access through DataManager

- [x] 6.1 Audit existing code for direct SQL queries

  - Review app.py and CLI scripts to identify any direct database access outside DataManager
  - Document all database operations that need to be moved to DataManager
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 6.2 Move all database operations to DataManager methods

  - Create new DataManager methods for any database operations found outside the class
  - Update all calling code to use DataManager methods instead of direct SQL
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Clean up redundant files and optimize project structure

- [x] 7.1 Remove redundant script files after CLI unification

  - Safely remove registrar_gasto.py and registrar_inversion.py after confirming functionality is preserved
  - Remove index_simple.html and any obsolete test files
  - _Requirements: 4.3_

- [x] 7.2 Generate requirements.txt and finalize project structure

  - Create requirements.txt with all Python dependencies and exact versions
  - Organize remaining files and ensure clean project structure
  - _Requirements: 4.4_

- [x] 8. Implement comprehensive testing for all new functionality


- [x] 8.1 Create unit tests for new configuration handling

  - Write tests for configuration validation, loading, and saving
  - Test automatic calculation functions for anexo totals
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.2, 6.3_

- [x] 8.2 Create integration tests for form and PDF generation

  - Test complete form submission workflow with new dynamic forms
  - Verify PDF generation with various data configurations
  - Test CLI unification and DataManager centralization
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 5.1, 5.2, 5.3_

-

- [x] 9. Validate and test migration from old to new system

- [x] 9.1 Test backward compatibility and data migration

  - Ensure existing configurations can be migrated to new format
  - Verify that all existing functionality continues to work
  - _Requirements: All requirements - comprehensive validation_

- [x] 9.2 Perform user acceptance testing

  - Test dynamic form usability and user experience
  - Validate PDF output quality and formatting
  - Confirm system performance with various data sizes
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 6.4_
