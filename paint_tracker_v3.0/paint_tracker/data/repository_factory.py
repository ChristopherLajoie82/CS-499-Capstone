"""
Repository Factory
Creates the right repository type based on database config (SQLite or PostgreSQL).

Author: Christopher Lajoie
"""

from typing import Tuple
from paint_tracker.config.database_config import DatabaseConfig


class RepositoryFactory:
    """Creates repository instances - picks SQLite or PostgreSQL based on config."""
    
    @staticmethod
    def create_job_repository():
        """
        Create and return appropriate JobRepository based on configuration.
        
        Returns:
            JobRepository instance (either SQLite or PostgreSQL)
            
        Raises:
            ConnectionError: If unable to connect to database
        """
        db_type = DatabaseConfig.get_database_type()
        
        if db_type == "sqlite":
            from paint_tracker.data.repository import JobRepository
            db_path = DatabaseConfig.get_sqlite_path()
            return JobRepository(db_path)
        
        elif db_type == "postgresql":
            from paint_tracker.data.repository_postgres import JobRepository
            params = DatabaseConfig.get_postgres_params()
            return JobRepository(params)
        
        else:
            raise ValueError(f"Unknown database type: {db_type}")
    
    @staticmethod
    def create_user_repository():
        """
        Create and return appropriate UserRepository based on configuration.
        
        Returns:
            UserRepository instance (either SQLite or PostgreSQL)
            
        Raises:
            ConnectionError: If unable to connect to database
        """
        db_type = DatabaseConfig.get_database_type()
        
        if db_type == "sqlite":
            from paint_tracker.data.user_repository import UserRepository
            db_path = DatabaseConfig.get_sqlite_path()
            return UserRepository(db_path)
        
        elif db_type == "postgresql":
            from paint_tracker.data.user_repository_postgres import UserRepository
            params = DatabaseConfig.get_postgres_params()
            return UserRepository(params)
        
        else:
            raise ValueError(f"Unknown database type: {db_type}")
    
    @staticmethod
    def test_connection() -> Tuple[bool, str]:
        """
        Test connection to the configured database.
        
        Returns:
            Tuple of (success, message)
        """
        db_type = DatabaseConfig.get_database_type()
        
        if db_type == "sqlite":
            try:
                import sqlite3
                from pathlib import Path
                db_path = DatabaseConfig.get_sqlite_path()
                
                # Test if we can open/create the database
                conn = sqlite3.connect(db_path)
                conn.close()
                return True, f"SQLite database accessible at {db_path}"
            except Exception as e:
                return False, f"SQLite connection failed: {str(e)}"
        
        elif db_type == "postgresql":
            return DatabaseConfig.test_postgres_connection()
        
        else:
            return False, f"Unknown database type: {db_type}"
