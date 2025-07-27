# -*- coding: utf-8 -*-
"""
Configuration validation module for PECO resolution generator.
Implements standardized data structure validation and integrity checks.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .base import Result
from .exceptions import ConfigurationError
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult(Result):
    """Result class for configuration validation operations."""
    validation_errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


class ConfigValidator:
    """
    Configuration validator for the standardized PECO resolution data structure.
    Validates mes_iso, structured considerandos, articulos arrays, and anexo objects.
    """
    
    def __init__(self):
        """Initialize the ConfigValidator."""
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_config_structure(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate the complete configuration structure according to the standardized schema.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            ValidationResult: Validation result with errors and warnings
        """
        self.logger.info("Starting configuration structure validation")
        
        errors = []
        warnings = []
        
        # Validate required top-level fields
        required_fields = ['mes_iso', 'titulo_base', 'visto', 'considerandos', 'articulos', 'anexo']
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
            elif config_data[field] is None:
                errors.append(f"Field cannot be null: {field}")
        
        # If basic structure is invalid, return early
        if errors:
            return ValidationResult(
                success=False,
                message=f"Configuration structure validation failed: {len(errors)} errors",
                validation_errors=errors,
                warnings=warnings
            )
        
        # Validate mes_iso format
        mes_iso_result = self._validate_mes_iso(config_data.get('mes_iso'))
        if not mes_iso_result.success:
            errors.extend(mes_iso_result.validation_errors or [])
        if mes_iso_result.warnings:
            warnings.extend(mes_iso_result.warnings)
        
        # Validate titulo_base
        titulo_result = self._validate_titulo_base(config_data.get('titulo_base'))
        if not titulo_result.success:
            errors.extend(titulo_result.validation_errors or [])
        if titulo_result.warnings:
            warnings.extend(titulo_result.warnings)
        
        # Validate visto
        visto_result = self._validate_visto(config_data.get('visto'))
        if not visto_result.success:
            errors.extend(visto_result.validation_errors or [])
        if visto_result.warnings:
            warnings.extend(visto_result.warnings)
        
        # Validate considerandos structure
        considerandos_result = self._validate_considerandos(config_data.get('considerandos'))
        if not considerandos_result.success:
            errors.extend(considerandos_result.validation_errors or [])
        if considerandos_result.warnings:
            warnings.extend(considerandos_result.warnings)
        
        # Validate articulos structure
        articulos_result = self._validate_articulos(config_data.get('articulos'))
        if not articulos_result.success:
            errors.extend(articulos_result.validation_errors or [])
        if articulos_result.warnings:
            warnings.extend(articulos_result.warnings)
        
        # Validate anexo structure
        anexo_result = self._validate_anexo(config_data.get('anexo'))
        if not anexo_result.success:
            errors.extend(anexo_result.validation_errors or [])
        if anexo_result.warnings:
            warnings.extend(anexo_result.warnings)
        
        # Determine overall success
        success = len(errors) == 0
        
        if success:
            message = "Configuration structure validation passed"
            if warnings:
                message += f" with {len(warnings)} warnings"
        else:
            message = f"Configuration structure validation failed: {len(errors)} errors"
            if warnings:
                message += f", {len(warnings)} warnings"
        
        return ValidationResult(
            success=success,
            message=message,
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_mes_iso(self, mes_iso: Any) -> ValidationResult:
        """Validate mes_iso field format (YYYY-MM)."""
        errors = []
        warnings = []
        
        if not isinstance(mes_iso, str):
            errors.append("mes_iso must be a string")
            return ValidationResult(success=False, message="mes_iso validation failed", validation_errors=errors)
        
        # Check format YYYY-MM
        if len(mes_iso) != 7 or mes_iso[4] != '-':
            errors.append("mes_iso must be in YYYY-MM format")
            return ValidationResult(success=False, message="mes_iso format validation failed", validation_errors=errors)
        
        try:
            year_str, month_str = mes_iso.split('-')
            year = int(year_str)
            month = int(month_str)
            
            # Validate year (reasonable range)
            current_year = datetime.now().year
            if year < 2020 or year > current_year + 5:
                warnings.append(f"mes_iso year {year} seems unusual (expected 2020-{current_year + 5})")
            
            # Validate month
            if month < 1 or month > 12:
                errors.append(f"mes_iso month {month} is invalid (must be 1-12)")
            
        except ValueError:
            errors.append("mes_iso contains invalid year or month values")
        
        success = len(errors) == 0
        message = "mes_iso validation passed" if success else "mes_iso validation failed"
        return ValidationResult(
            success=success,
            message=message,
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_titulo_base(self, titulo_base: Any) -> ValidationResult:
        """Validate titulo_base field."""
        errors = []
        warnings = []
        
        if not isinstance(titulo_base, str):
            errors.append("titulo_base must be a string")
        elif len(titulo_base.strip()) == 0:
            errors.append("titulo_base cannot be empty")
        elif len(titulo_base) > 200:
            warnings.append("titulo_base is very long (>200 characters)")
        
        success = len(errors) == 0
        message = "titulo_base validation passed" if success else "titulo_base validation failed"
        return ValidationResult(
            success=success,
            message=message,
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_visto(self, visto: Any) -> ValidationResult:
        """Validate visto field."""
        errors = []
        warnings = []
        
        if not isinstance(visto, str):
            errors.append("visto must be a string")
        elif len(visto.strip()) == 0:
            errors.append("visto cannot be empty")
        elif len(visto) > 1000:
            warnings.append("visto is very long (>1000 characters)")
        
        success = len(errors) == 0
        message = "visto validation passed" if success else "visto validation failed"
        return ValidationResult(
            success=success,
            message=message,
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_considerandos(self, considerandos: Any) -> ValidationResult:
        """Validate considerandos array structure."""
        errors = []
        warnings = []
        
        if not isinstance(considerandos, list):
            errors.append("considerandos must be an array")
            return ValidationResult(success=False, message="considerandos validation failed", validation_errors=errors)
        
        if len(considerandos) == 0:
            warnings.append("considerandos array is empty")
        
        for i, considerando in enumerate(considerandos):
            if not isinstance(considerando, dict):
                errors.append(f"considerandos[{i}] must be an object")
                continue
            
            # Validate tipo field
            if 'tipo' not in considerando:
                errors.append(f"considerandos[{i}] missing required field 'tipo'")
            elif considerando['tipo'] not in ['gasto_anterior', 'texto']:
                errors.append(f"considerandos[{i}] tipo must be 'gasto_anterior' or 'texto'")
            
            # Validate based on tipo
            if considerando.get('tipo') == 'gasto_anterior':
                if 'descripcion' not in considerando:
                    errors.append(f"considerandos[{i}] with tipo 'gasto_anterior' missing 'descripcion'")
                elif not isinstance(considerando['descripcion'], str) or len(considerando['descripcion'].strip()) == 0:
                    errors.append(f"considerandos[{i}] descripcion must be a non-empty string")
                
                if 'monto' not in considerando:
                    errors.append(f"considerandos[{i}] with tipo 'gasto_anterior' missing 'monto'")
                elif not self._is_valid_amount(considerando['monto']):
                    errors.append(f"considerandos[{i}] monto must be a valid numeric string")
                
                # Check for unexpected fields
                if 'contenido' in considerando:
                    warnings.append(f"considerandos[{i}] with tipo 'gasto_anterior' has unexpected 'contenido' field")
            
            elif considerando.get('tipo') == 'texto':
                if 'contenido' not in considerando:
                    errors.append(f"considerandos[{i}] with tipo 'texto' missing 'contenido'")
                elif not isinstance(considerando['contenido'], str) or len(considerando['contenido'].strip()) == 0:
                    errors.append(f"considerandos[{i}] contenido must be a non-empty string")
                
                # Check for unexpected fields
                if 'descripcion' in considerando or 'monto' in considerando:
                    warnings.append(f"considerandos[{i}] with tipo 'texto' has unexpected fields (descripcion/monto)")
        
        success = len(errors) == 0
        return ValidationResult(
            success=success,
            message="validation completed",
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_articulos(self, articulos: Any) -> ValidationResult:
        """Validate articulos array structure."""
        errors = []
        warnings = []
        
        if not isinstance(articulos, list):
            errors.append("articulos must be an array")
            return ValidationResult(success=False, message="articulos validation failed", validation_errors=errors)
        
        if len(articulos) == 0:
            warnings.append("articulos array is empty")
        
        for i, articulo in enumerate(articulos):
            if not isinstance(articulo, str):
                errors.append(f"articulos[{i}] must be a string")
            elif len(articulo.strip()) == 0:
                errors.append(f"articulos[{i}] cannot be empty")
            elif len(articulo) > 500:
                warnings.append(f"articulos[{i}] is very long (>500 characters)")
        
        success = len(errors) == 0
        return ValidationResult(
            success=success,
            message="validation completed",
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_anexo(self, anexo: Any) -> ValidationResult:
        """Validate anexo object structure."""
        errors = []
        warnings = []
        
        if not isinstance(anexo, dict):
            errors.append("anexo must be an object")
            return ValidationResult(success=False, message="anexo validation failed", validation_errors=errors)
        
        # Validate required fields - support both 'items' and 'presupuesto' for backward compatibility
        required_fields = ['titulo', 'penalizaciones', 'nota_final']
        for field in required_fields:
            if field not in anexo:
                errors.append(f"anexo missing required field: {field}")
        
        # Check for anexo_items or presupuesto field
        if 'anexo_items' not in anexo and 'presupuesto' not in anexo:
            errors.append("anexo missing required field: 'anexo_items' or 'presupuesto'")
        elif 'anexo_items' in anexo and 'presupuesto' in anexo:
            warnings.append("anexo has both 'anexo_items' and 'presupuesto' fields - 'anexo_items' will be used")
        
        # Validate titulo
        if 'titulo' in anexo:
            if not isinstance(anexo['titulo'], str):
                errors.append("anexo.titulo must be a string")
            elif len(anexo['titulo'].strip()) == 0:
                errors.append("anexo.titulo cannot be empty")
        
        # Validate anexo_items array (preferred) or presupuesto array (backward compatibility)
        items_field = 'anexo_items' if 'anexo_items' in anexo else 'presupuesto'
        if items_field in anexo:
            items_result = self._validate_anexo_items(anexo[items_field], items_field)
            if not items_result.success:
                errors.extend(items_result.validation_errors or [])
            if items_result.warnings:
                warnings.extend(items_result.warnings)
        
        # Validate penalizaciones array
        if 'penalizaciones' in anexo:
            penalizaciones_result = self._validate_anexo_items(anexo['penalizaciones'], 'penalizaciones')
            if not penalizaciones_result.success:
                errors.extend(penalizaciones_result.validation_errors or [])
            if penalizaciones_result.warnings:
                warnings.extend(penalizaciones_result.warnings)
        
        # Validate nota_final
        if 'nota_final' in anexo:
            if not isinstance(anexo['nota_final'], str):
                errors.append("anexo.nota_final must be a string")
            # nota_final can be empty, so no empty check
        
        success = len(errors) == 0
        return ValidationResult(
            success=success,
            message="validation completed",
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _validate_anexo_items(self, items: Any, field_name: str) -> ValidationResult:
        """Validate anexo items or penalizaciones array."""
        errors = []
        warnings = []
        
        if not isinstance(items, list):
            errors.append(f"anexo.{field_name} must be an array")
            return ValidationResult(success=False, message=f"anexo.{field_name} validation failed", validation_errors=errors)
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"anexo.{field_name}[{i}] must be an object")
                continue
            
            # Validate required fields
            if 'categoria' not in item:
                errors.append(f"anexo.{field_name}[{i}] missing required field 'categoria'")
            elif not isinstance(item['categoria'], str) or len(item['categoria'].strip()) == 0:
                errors.append(f"anexo.{field_name}[{i}] categoria must be a non-empty string")
            
            if 'monto' not in item:
                errors.append(f"anexo.{field_name}[{i}] missing required field 'monto'")
            elif not self._is_valid_amount(item['monto']):
                errors.append(f"anexo.{field_name}[{i}] monto must be a valid numeric string")
            
            # For penalizaciones, amounts should typically be negative
            if field_name == 'penalizaciones' and 'monto' in item:
                try:
                    amount = float(item['monto'])
                    if amount > 0:
                        warnings.append(f"anexo.{field_name}[{i}] monto is positive (penalizaciones are typically negative)")
                except (ValueError, TypeError):
                    pass  # Already handled by _is_valid_amount
        
        success = len(errors) == 0
        return ValidationResult(
            success=success,
            message="validation completed",
            validation_errors=errors if errors else None,
            warnings=warnings if warnings else None
        )
    
    def _is_valid_amount(self, amount: Any) -> bool:
        """Check if amount is a valid numeric string."""
        if not isinstance(amount, str):
            return False
        
        try:
            # Remove common formatting characters
            cleaned_amount = amount.replace(',', '').replace(' ', '').replace('-', '', 1)  # Allow one minus sign
            float(cleaned_amount)
            return True
        except (ValueError, TypeError):
            return False
    
    def calculate_anexo_totals(self, anexo: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate subtotals and final amounts for anexo items.
        Supports both 'items' and 'presupuesto' fields for backward compatibility.
        
        Args:
            anexo: Anexo object with items/presupuesto and penalizaciones
            
        Returns:
            Dict with calculated totals
        """
        self.logger.info("Calculating anexo totals")
        
        subtotal = 0.0
        penalizaciones_total = 0.0
        
        # Calculate items subtotal - support both 'anexo_items' and 'presupuesto'
        items_field = 'anexo_items' if 'anexo_items' in anexo else 'presupuesto'
        if items_field in anexo and isinstance(anexo[items_field], list):
            for item in anexo[items_field]:
                if isinstance(item, dict) and 'monto' in item:
                    try:
                        # Clean amount string: remove currency symbols, commas, spaces
                        amount_str = str(item['monto']).replace('$', '').replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        subtotal += amount
                        self.logger.debug(f"Added item amount: {amount} from {item.get('categoria', 'unknown')}")
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid amount in anexo {items_field}: {item.get('monto')}")
        
        # Calculate penalizaciones total
        if 'penalizaciones' in anexo and isinstance(anexo['penalizaciones'], list):
            for penalizacion in anexo['penalizaciones']:
                if isinstance(penalizacion, dict) and 'monto' in penalizacion:
                    try:
                        # Clean amount string and handle negative values
                        amount_str = str(penalizacion['monto']).replace('$', '').replace(',', '').replace(' ', '').strip()
                        
                        # Handle negative values properly
                        if amount_str.startswith('-'):
                            amount = float(amount_str[1:])  # Remove negative sign for calculation
                        else:
                            amount = float(amount_str)
                        
                        penalizaciones_total += amount
                        self.logger.debug(f"Added penalizacion amount: {amount} from {penalizacion.get('categoria', 'unknown')}")
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid amount in penalizacion: {penalizacion.get('monto')}")
        
        # Calculate final total (subtract penalizaciones from subtotal)
        total_solicitado = subtotal - penalizaciones_total
        
        self.logger.info(f"Calculated totals - Subtotal: {subtotal}, Penalizaciones: {penalizaciones_total}, Total: {total_solicitado}")
        
        return {
            'subtotal': subtotal,
            'penalizaciones_total': penalizaciones_total,
            'total_solicitado': total_solicitado
        }
    
    def validate_and_load_config(self, file_path: str) -> ValidationResult:
        """
        Load and validate configuration file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            ValidationResult with loaded and validated data
        """
        self.logger.info(f"Loading and validating configuration from: {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return ValidationResult(
                    success=False,
                    message=f"Configuration file not found: {file_path}",
                    validation_errors=[f"File not found: {file_path}"]
                )
            
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate structure
            validation_result = self.validate_config_structure(config_data)
            
            if validation_result.success:
                # Add calculated totals to anexo if validation passed
                if 'anexo' in config_data:
                    totals = self.calculate_anexo_totals(config_data['anexo'])
                    config_data['anexo'].update(totals)
                
                validation_result.data = config_data
                validation_result.message = f"Configuration loaded and validated successfully from {file_path}"
                if validation_result.warnings:
                    validation_result.message += f" with {len(validation_result.warnings)} warnings"
            
            return validation_result
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                success=False,
                message=f"Invalid JSON in configuration file: {str(e)}",
                validation_errors=[f"JSON decode error: {str(e)}"]
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Error loading configuration: {str(e)}",
                validation_errors=[f"Load error: {str(e)}"]
            )
    
    def save_validated_config(self, config_data: Dict[str, Any], file_path: str) -> ValidationResult:
        """
        Validate and save configuration data to file.
        
        Args:
            config_data: Configuration data to validate and save
            file_path: Path to save configuration file
            
        Returns:
            ValidationResult indicating success or failure
        """
        self.logger.info(f"Validating and saving configuration to: {file_path}")
        
        # First validate the structure
        validation_result = self.validate_config_structure(config_data)
        
        if not validation_result.success:
            return validation_result
        
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(file_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                self.logger.info(f"Created configuration directory: {config_dir}")
            
            # Calculate and add totals to anexo before saving
            if 'anexo' in config_data:
                totals = self.calculate_anexo_totals(config_data['anexo'])
                config_data['anexo'].update(totals)
            
            # Save configuration with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Configuration saved successfully")
            
            validation_result.message = f"Configuration validated and saved successfully to {file_path}"
            if validation_result.warnings:
                validation_result.message += f" with {len(validation_result.warnings)} warnings"
            
            return validation_result
            
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Error saving configuration: {str(e)}",
                validation_errors=[f"Save error: {str(e)}"]
            )
    
    def process_configuration_for_template(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        Process configuration data for template rendering.
        Adds calculated values, formats dates, and prepares data for LaTeX template.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            ValidationResult with processed configuration data
        """
        self.logger.info("Processing configuration for template rendering")
        
        try:
            # Create a deep copy to avoid modifying original data
            import copy
            processed_config = copy.deepcopy(config_data)
            
            # Normalize configuration structure first
            normalize_result = self.normalize_configuration_structure(processed_config)
            if normalize_result.success:
                processed_config = normalize_result.data
            
            # Process mes_iso to get month name and year
            if 'mes_iso' in processed_config:
                try:
                    fecha_iso = datetime.strptime(processed_config['mes_iso'], '%Y-%m')
                    
                    # Spanish month names
                    meses_nombres = {
                        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
                        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
                        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
                    }
                    
                    processed_config['mes_nombre'] = meses_nombres[fecha_iso.month]
                    processed_config['anio'] = str(fecha_iso.year)
                    
                    self.logger.debug(f"Processed date: {processed_config['mes_nombre']} {processed_config['anio']}")
                    
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing mes_iso: {e}")
                    processed_config['mes_nombre'] = "mes"
                    processed_config['anio'] = "año"
            
            # Calculate anexo totals and add to configuration
            if 'anexo' in processed_config:
                totals = self.calculate_anexo_totals(processed_config['anexo'])
                processed_config['anexo'].update(totals)
                
                # Format totals as strings for template
                processed_config['anexo']['subtotal'] = f"{totals['subtotal']:.0f}"
                processed_config['anexo']['total_solicitado'] = f"{totals['total_solicitado']:.0f}"
            
            # Replace MONTO_TOTAL placeholder in articulos
            if 'anexo' in processed_config and 'total_solicitado' in processed_config['anexo']:
                total_monto = processed_config['anexo']['total_solicitado']
                if 'articulos' in processed_config:
                    for i, articulo in enumerate(processed_config['articulos']):
                        processed_config['articulos'][i] = articulo.replace('$MONTO_TOTAL', total_monto)
            
            # Generate resolution code and date information
            fecha_actual = datetime.now()
            dia = fecha_actual.day
            
            # Roman numerals for months
            meses_romanos = {
                1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
                7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"
            }
            
            mes_romano = meses_romanos[fecha_actual.month]
            año_corto = fecha_actual.strftime('%y')
            codigo_res = f"r{dia}e{mes_romano}s{año_corto}"
            
            processed_config['codigo_res'] = codigo_res
            processed_config['fecha_larga'] = fecha_actual.strftime(f'%d de {processed_config.get("mes_nombre", "mes")} de %Y')
            processed_config['titulo_documento'] = f"{codigo_res} - {processed_config.get('titulo_base', 'Resolución')}"
            
            self.logger.info(f"Generated resolution code: {codigo_res}")
            
            return ValidationResult(
                success=True,
                message="Configuration processed successfully for template rendering",
                data=processed_config
            )
            
        except Exception as e:
            self.logger.error(f"Error processing configuration for template: {e}")
            return ValidationResult(
                success=False,
                message=f"Error processing configuration for template: {str(e)}",
                validation_errors=[f"Processing error: {str(e)}"]
            )
    
    def normalize_configuration_structure(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        Normalize configuration structure to the standardized format.
        Converts 'presupuesto' to 'items' for backward compatibility.
        
        Args:
            config_data: Configuration data to normalize
            
        Returns:
            ValidationResult with normalized configuration data
        """
        self.logger.info("Normalizing configuration structure")
        
        try:
            # Create a deep copy to avoid modifying original data
            import copy
            normalized_config = copy.deepcopy(config_data)
            
            # Normalize anexo structure
            if 'anexo' in normalized_config and isinstance(normalized_config['anexo'], dict):
                anexo = copy.deepcopy(normalized_config['anexo'])
                
                # Convert 'presupuesto' to 'anexo_items' to avoid conflict with dict.items() method
                if 'presupuesto' in anexo and 'anexo_items' not in anexo:
                    anexo['anexo_items'] = anexo['presupuesto']
                    del anexo['presupuesto']
                    self.logger.info("Converted 'presupuesto' field to 'anexo_items' for standardization")
                
                normalized_config['anexo'] = anexo
            
            return ValidationResult(
                success=True,
                message="Configuration structure normalized successfully",
                data=normalized_config
            )
            
        except Exception as e:
            self.logger.error(f"Error normalizing configuration structure: {e}")
            return ValidationResult(
                success=False,
                message=f"Error normalizing configuration structure: {str(e)}",
                validation_errors=[f"Normalization error: {str(e)}"]
            )