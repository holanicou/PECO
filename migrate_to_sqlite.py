#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PECO Database Migration Script
Migrates existing CSV and Excel data to SQLite database.
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import DatabaseManager
from services.logging_config import get_logger
import config

logger = get_logger(__name__)


def main():
    """Main migration function."""
    print("🔄 PECO Database Migration Tool")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager("peco.db")
    
    # Check if data files exist
    csv_exists = os.path.exists(config.CSV_GASTOS)
    xlsx_exists = os.path.exists(config.XLSX_INVERSIONES)
    
    print(f"📁 Archivos de datos:")
    print(f"   Gastos CSV: {'✓' if csv_exists else '✗'} {config.CSV_GASTOS}")
    print(f"   Inversiones Excel: {'✓' if xlsx_exists else '✗'} {config.XLSX_INVERSIONES}")
    
    if not csv_exists and not xlsx_exists:
        print("\n⚠️  No se encontraron archivos de datos para migrar.")
        print("   La base de datos SQLite está lista para usar.")
        return
    
    # Ask for confirmation
    print(f"\n🎯 Se migrará la data a: peco.db")
    response = input("¿Continuar con la migración? (s/N): ").lower().strip()
    
    if response not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Migración cancelada.")
        return
    
    # Perform migration
    print("\n🚀 Iniciando migración...")
    
    try:
        result = db_manager.migrate_from_csv_excel(
            config.CSV_GASTOS,
            config.XLSX_INVERSIONES
        )
        
        if result.success:
            print(f"✅ {result.message}")
            
            # Show statistics
            stats_result = db_manager.get_database_stats()
            if stats_result.success:
                stats = stats_result.data
                print(f"\n📊 Estadísticas de la base de datos:")
                print(f"   Total gastos: {stats['total_expenses']}")
                print(f"   Total inversiones: {stats['total_investments']}")
                print(f"   Total registros: {stats['total_records']}")
                print(f"   Tamaño: {stats['database_size_mb']} MB")
            
            # Ask about backup
            print(f"\n💾 ¿Crear backup de los archivos originales?")
            backup_response = input("   Esto los renombrará con .backup (s/N): ").lower().strip()
            
            if backup_response in ['s', 'si', 'sí', 'y', 'yes']:
                backup_files(csv_exists, xlsx_exists)
            
            print(f"\n🎉 ¡Migración completada exitosamente!")
            print(f"   Tu aplicación ahora usará SQLite para mejor rendimiento.")
            
        else:
            print(f"❌ Error en migración: {result.message}")
            if hasattr(result, 'error_code'):
                print(f"   Código de error: {result.error_code}")
    
    except Exception as e:
        logger.error(f"Migration script error: {e}")
        print(f"❌ Error inesperado: {e}")


def backup_files(csv_exists: bool, xlsx_exists: bool):
    """Backup original files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if csv_exists:
            backup_path = f"{config.CSV_GASTOS}.backup_{timestamp}"
            os.rename(config.CSV_GASTOS, backup_path)
            print(f"   ✓ CSV respaldado: {backup_path}")
        
        if xlsx_exists:
            backup_path = f"{config.XLSX_INVERSIONES}.backup_{timestamp}"
            os.rename(config.XLSX_INVERSIONES, backup_path)
            print(f"   ✓ Excel respaldado: {backup_path}")
            
    except Exception as e:
        print(f"   ⚠️  Error creando backup: {e}")


def test_database():
    """Test database functionality."""
    print("\n🧪 Probando funcionalidad de la base de datos...")
    
    db_manager = DatabaseManager("peco_test.db")
    
    # Test adding expense
    result = db_manager.add_expense("2025-01-25", "Prueba", "Gasto de prueba", 100.0)
    if result.success:
        print("   ✓ Inserción de gasto: OK")
    else:
        print(f"   ✗ Inserción de gasto: {result.message}")
    
    # Test adding investment
    result = db_manager.add_investment("2025-01-25", "TEST", "Compra", 500.0)
    if result.success:
        print("   ✓ Inserción de inversión: OK")
    else:
        print(f"   ✗ Inserción de inversión: {result.message}")
    
    # Test monthly summary
    result = db_manager.get_monthly_summary(2025, 1)
    if result.success:
        print("   ✓ Resumen mensual: OK")
        print(f"     Gastos: ${result.data['total_expenses']}")
        print(f"     Inversiones netas: ${result.data['net_investment']}")
    else:
        print(f"   ✗ Resumen mensual: {result.message}")
    
    # Clean up test database
    try:
        os.remove("peco_test.db")
        print("   ✓ Base de datos de prueba eliminada")
    except:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_database()
    else:
        main()