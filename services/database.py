# -*- coding: utf-8 -*-
"""
Database manager for PECO financial application.
Handles SQLite database operations and data migration.
"""

import sqlite3
import os
import csv
import pandas as pd
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .base import Result
from .exceptions import DataError
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseResult(Result):
    """Result class for database operations."""
    data: Optional[Any] = None
    affected_rows: Optional[int] = None


class DatabaseManager:
    """
    SQLite database manager for PECO financial data.
    Handles database creation, migrations, and CRUD operations.
    """
    
    def __init__(self, db_path: str = "peco.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = get_logger(self.__class__.__name__)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise DataError(f"Database connection failed: {str(e)}", "DB_CONNECTION_ERROR")
        finally:
            if conn:
                conn.close()
    
    def init_database(self) -> DatabaseResult:
        """
        Initialize the database with required tables.
        
        Returns:
            DatabaseResult: Result of database initialization
        """
        try:
            self.logger.info(f"Initializing database at: {self.db_path}")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create expenses table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha DATE NOT NULL,
                        categoria TEXT NOT NULL,
                        descripcion TEXT NOT NULL,
                        monto_ars REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create investments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha DATE NOT NULL,
                        activo TEXT NOT NULL,
                        tipo TEXT NOT NULL CHECK (tipo IN ('Compra', 'Venta')),
                        monto_ars REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_fecha ON expenses(fecha)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_categoria ON expenses(categoria)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_investments_fecha ON investments(fecha)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_investments_activo ON investments(activo)')
                
                # Create trigger to update updated_at timestamp
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_expenses_timestamp 
                    AFTER UPDATE ON expenses
                    BEGIN
                        UPDATE expenses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                ''')
                
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_investments_timestamp 
                    AFTER UPDATE ON investments
                    BEGIN
                        UPDATE investments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                ''')
                
                conn.commit()
                
            self.logger.info("Database initialized successfully")
            return DatabaseResult(
                success=True,
                message="Database initialized successfully"
            )
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return DatabaseResult(
                success=False,
                message=f"Database initialization failed: {str(e)}",
                error_code="DB_INIT_ERROR"
            )
    
    def add_expense(self, fecha: str, categoria: str, descripcion: str, monto_ars: float) -> DatabaseResult:
        """
        Add a new expense to the database.
        
        Args:
            fecha: Date in YYYY-MM-DD format
            categoria: Expense category
            descripcion: Expense description
            monto_ars: Amount in ARS
            
        Returns:
            DatabaseResult: Result of the operation
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO expenses (fecha, categoria, descripcion, monto_ars)
                    VALUES (?, ?, ?, ?)
                ''', (fecha, categoria, descripcion, monto_ars))
                
                expense_id = cursor.lastrowid
                conn.commit()
                
            self.logger.info(f"Expense added successfully with ID: {expense_id}")
            return DatabaseResult(
                success=True,
                message=f"Gasto registrado exitosamente (ID: {expense_id})",
                data={'id': expense_id},
                affected_rows=1
            )
            
        except Exception as e:
            self.logger.error(f"Failed to add expense: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error registrando gasto: {str(e)}",
                error_code="EXPENSE_INSERT_ERROR"
            )
    
    def add_investment(self, fecha: str, activo: str, tipo: str, monto_ars: float) -> DatabaseResult:
        """
        Add a new investment to the database.
        
        Args:
            fecha: Date in YYYY-MM-DD format
            activo: Asset name
            tipo: Transaction type ('Compra' or 'Venta')
            monto_ars: Amount in ARS
            
        Returns:
            DatabaseResult: Result of the operation
        """
        try:
            if tipo not in ['Compra', 'Venta']:
                return DatabaseResult(
                    success=False,
                    message="Tipo debe ser 'Compra' o 'Venta'",
                    error_code="INVALID_INVESTMENT_TYPE"
                )
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO investments (fecha, activo, tipo, monto_ars)
                    VALUES (?, ?, ?, ?)
                ''', (fecha, activo, tipo, monto_ars))
                
                investment_id = cursor.lastrowid
                conn.commit()
                
            self.logger.info(f"Investment added successfully with ID: {investment_id}")
            return DatabaseResult(
                success=True,
                message=f"Inversión registrada exitosamente (ID: {investment_id})",
                data={'id': investment_id},
                affected_rows=1
            )
            
        except Exception as e:
            self.logger.error(f"Failed to add investment: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error registrando inversión: {str(e)}",
                error_code="INVESTMENT_INSERT_ERROR"
            )
    
    def get_expenses_by_month(self, year: int, month: int) -> DatabaseResult:
        """
        Get all expenses for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            DatabaseResult: Result with expenses data
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, fecha, categoria, descripcion, monto_ars, created_at
                    FROM expenses
                    WHERE strftime('%Y', fecha) = ? AND strftime('%m', fecha) = ?
                    ORDER BY fecha DESC, created_at DESC
                ''', (str(year), f"{month:02d}"))
                
                expenses = [dict(row) for row in cursor.fetchall()]
                
            return DatabaseResult(
                success=True,
                message=f"Encontrados {len(expenses)} gastos para {month}/{year}",
                data=expenses
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get expenses: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error obteniendo gastos: {str(e)}",
                error_code="EXPENSES_QUERY_ERROR"
            )
    
    def get_investments_by_month(self, year: int, month: int) -> DatabaseResult:
        """
        Get all investments for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            DatabaseResult: Result with investments data
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, fecha, activo, tipo, monto_ars, created_at
                    FROM investments
                    WHERE strftime('%Y', fecha) = ? AND strftime('%m', fecha) = ?
                    ORDER BY fecha DESC, created_at DESC
                ''', (str(year), f"{month:02d}"))
                
                investments = [dict(row) for row in cursor.fetchall()]
                
            return DatabaseResult(
                success=True,
                message=f"Encontradas {len(investments)} inversiones para {month}/{year}",
                data=investments
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get investments: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error obteniendo inversiones: {str(e)}",
                error_code="INVESTMENTS_QUERY_ERROR"
            )
    
    def get_expenses_by_category(self, year: int, month: int) -> DatabaseResult:
        """
        Get expenses grouped by category for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            DatabaseResult: Result with categorized expenses
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT categoria, SUM(monto_ars) as total, COUNT(*) as count
                    FROM expenses
                    WHERE strftime('%Y', fecha) = ? AND strftime('%m', fecha) = ?
                    GROUP BY categoria
                    ORDER BY total DESC
                ''', (str(year), f"{month:02d}"))
                
                categories = [dict(row) for row in cursor.fetchall()]
                
            return DatabaseResult(
                success=True,
                message=f"Encontradas {len(categories)} categorías para {month}/{year}",
                data=categories
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get expenses by category: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error obteniendo gastos por categoría: {str(e)}",
                error_code="CATEGORY_QUERY_ERROR"
            )
    
    def get_monthly_summary(self, year: int, month: int) -> DatabaseResult:
        """
        Get monthly financial summary.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            DatabaseResult: Result with monthly summary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total expenses
                cursor.execute('''
                    SELECT COALESCE(SUM(monto_ars), 0) as total_expenses, COUNT(*) as expense_count
                    FROM expenses
                    WHERE strftime('%Y', fecha) = ? AND strftime('%m', fecha) = ?
                ''', (str(year), f"{month:02d}"))
                expense_data = dict(cursor.fetchone())
                
                # Get total investments
                cursor.execute('''
                    SELECT 
                        COALESCE(SUM(CASE WHEN tipo = 'Compra' THEN monto_ars ELSE 0 END), 0) as total_purchases,
                        COALESCE(SUM(CASE WHEN tipo = 'Venta' THEN monto_ars ELSE 0 END), 0) as total_sales,
                        COUNT(*) as investment_count
                    FROM investments
                    WHERE strftime('%Y', fecha) = ? AND strftime('%m', fecha) = ?
                ''', (str(year), f"{month:02d}"))
                investment_data = dict(cursor.fetchone())
                
                summary = {
                    'year': year,
                    'month': month,
                    'total_expenses': expense_data['total_expenses'],
                    'expense_count': expense_data['expense_count'],
                    'total_purchases': investment_data['total_purchases'],
                    'total_sales': investment_data['total_sales'],
                    'net_investment': investment_data['total_purchases'] - investment_data['total_sales'],
                    'investment_count': investment_data['investment_count']
                }
                
            return DatabaseResult(
                success=True,
                message=f"Resumen mensual generado para {month}/{year}",
                data=summary
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get monthly summary: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error generando resumen mensual: {str(e)}",
                error_code="SUMMARY_QUERY_ERROR"
            )
    
    def migrate_from_csv_excel(self, csv_gastos_path: str, xlsx_inversiones_path: str) -> DatabaseResult:
        """
        Migrate data from existing CSV and Excel files to SQLite database.
        
        Args:
            csv_gastos_path: Path to expenses CSV file
            xlsx_inversiones_path: Path to investments Excel file
            
        Returns:
            DatabaseResult: Result of migration operation
        """
        try:
            migrated_expenses = 0
            migrated_investments = 0
            
            # Migrate expenses from CSV
            if os.path.exists(csv_gastos_path):
                self.logger.info(f"Migrating expenses from: {csv_gastos_path}")
                with open(csv_gastos_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Map CSV columns to database columns
                        fecha = row.get('Fecha', '')
                        categoria = row.get('Categoria', '')
                        descripcion = row.get('Descripcion', '')
                        monto_str = row.get('Monto_ARS', '0')
                        
                        try:
                            monto_ars = float(monto_str)
                            result = self.add_expense(fecha, categoria, descripcion, monto_ars)
                            if result.success:
                                migrated_expenses += 1
                        except ValueError:
                            self.logger.warning(f"Skipping invalid expense row: {row}")
            
            # Migrate investments from Excel
            if os.path.exists(xlsx_inversiones_path):
                self.logger.info(f"Migrating investments from: {xlsx_inversiones_path}")
                try:
                    df = pd.read_excel(xlsx_inversiones_path)
                    for _, row in df.iterrows():
                        fecha = str(row.get('Fecha', ''))
                        activo = str(row.get('Activo', ''))
                        tipo = str(row.get('Tipo', ''))
                        monto_ars = float(row.get('Monto_ARS', 0))
                        
                        result = self.add_investment(fecha, activo, tipo, monto_ars)
                        if result.success:
                            migrated_investments += 1
                except Exception as e:
                    self.logger.warning(f"Error reading Excel file: {e}")
            
            message = f"Migración completada: {migrated_expenses} gastos, {migrated_investments} inversiones"
            self.logger.info(message)
            
            return DatabaseResult(
                success=True,
                message=message,
                data={
                    'migrated_expenses': migrated_expenses,
                    'migrated_investments': migrated_investments
                }
            )
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error en migración: {str(e)}",
                error_code="MIGRATION_ERROR"
            )
    
    def backup_to_csv_excel(self, csv_path: str, xlsx_path: str) -> DatabaseResult:
        """
        Backup database data to CSV and Excel files.
        
        Args:
            csv_path: Path for expenses CSV backup
            xlsx_path: Path for investments Excel backup
            
        Returns:
            DatabaseResult: Result of backup operation
        """
        try:
            # Backup expenses to CSV
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT fecha, categoria, descripcion, monto_ars FROM expenses ORDER BY fecha')
                expenses = cursor.fetchall()
                
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Fecha', 'Categoria', 'Descripcion', 'Monto_ARS'])
                    for expense in expenses:
                        writer.writerow(expense)
                
                # Backup investments to Excel
                cursor.execute('SELECT fecha, activo, tipo, monto_ars FROM investments ORDER BY fecha')
                investments = cursor.fetchall()
                
                df = pd.DataFrame(investments, columns=['Fecha', 'Activo', 'Tipo', 'Monto_ARS'])
                df.to_excel(xlsx_path, index=False, sheet_name='Inversiones')
            
            return DatabaseResult(
                success=True,
                message=f"Backup completado: {len(expenses)} gastos, {len(investments)} inversiones",
                data={
                    'expenses_backed_up': len(expenses),
                    'investments_backed_up': len(investments)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error en backup: {str(e)}",
                error_code="BACKUP_ERROR"
            )
    
    def get_database_stats(self) -> DatabaseResult:
        """
        Get database statistics.
        
        Returns:
            DatabaseResult: Result with database statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table counts
                cursor.execute('SELECT COUNT(*) FROM expenses')
                expense_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM investments')
                investment_count = cursor.fetchone()[0]
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                stats = {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'total_expenses': expense_count,
                    'total_investments': investment_count,
                    'total_records': expense_count + investment_count
                }
                
            return DatabaseResult(
                success=True,
                message="Estadísticas de base de datos obtenidas",
                data=stats
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return DatabaseResult(
                success=False,
                message=f"Error obteniendo estadísticas: {str(e)}",
                error_code="STATS_ERROR"
            )