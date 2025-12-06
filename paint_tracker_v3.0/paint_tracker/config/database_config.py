"""
Database Configuration
Settings for SQLite and PostgreSQL database connections.

Author: Christopher Lajoie
"""

import os
import json
from typing import Dict, Optional
from pathlib import Path


class DatabaseConfig:
    """Manages database settings - supports both SQLite and PostgreSQL."""
    
    # Default configuration file location
    CONFIG_DIR = Path.home() / ".paint_tracker"
    CONFIG_FILE = CONFIG_DIR / "database_config.json"
    
    # Default SQLite path
    DEFAULT_SQLITE_PATH = str(Path.home() / "paint_tracker.db")
    
    # Default PostgreSQL settings
    DEFAULT_POSTGRES = {
        "host": "localhost",
        "port": 5432,
        "database": "paint_tracker",
        "user": "paint_user",
        "password": ""
    }
    
    @classmethod
    def load_config(cls) -> Dict:
        """
        Load database configuration from file.
        Returns default config if file doesn't exist.
        """
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return cls._get_default_config()
        return cls._get_default_config()
    
    @classmethod
    def save_config(cls, config: Dict) -> bool:
        """
        Save database configuration to file.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception:
            return False
    
    @classmethod
    def _get_default_config(cls) -> Dict:
        """Get default configuration (SQLite)"""
        return {
            "database_type": "sqlite",  # or "postgresql"
            "sqlite": {
                "path": cls.DEFAULT_SQLITE_PATH
            },
            "postgresql": cls.DEFAULT_POSTGRES.copy()
        }
    
    @classmethod
    def get_database_type(cls) -> str:
        """Get configured database type ('sqlite' or 'postgresql')"""
        config = cls.load_config()
        return config.get("database_type", "sqlite")
    
    @classmethod
    def get_sqlite_path(cls) -> str:
        """Get SQLite database path"""
        config = cls.load_config()
        return config.get("sqlite", {}).get("path", cls.DEFAULT_SQLITE_PATH)
    
    @classmethod
    def get_postgres_params(cls) -> Dict[str, str]:
        """Get PostgreSQL connection parameters"""
        config = cls.load_config()
        return config.get("postgresql", cls.DEFAULT_POSTGRES.copy())
    
    @classmethod
    def set_database_type(cls, db_type: str) -> bool:
        """
        Set the database type to use.
        
        Args:
            db_type: Either 'sqlite' or 'postgresql'
            
        Returns:
            True if successful
        """
        if db_type not in ('sqlite', 'postgresql'):
            return False
        
        config = cls.load_config()
        config["database_type"] = db_type
        return cls.save_config(config)
    
    @classmethod
    def set_postgres_params(cls, host: str, port: int, database: str, 
                           user: str, password: str) -> bool:
        """
        Set PostgreSQL connection parameters.
        
        Args:
            host: Database server hostname
            port: Database server port
            database: Database name
            user: Username
            password: Password
            
        Returns:
            True if successful
        """
        config = cls.load_config()
        config["postgresql"] = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        return cls.save_config(config)
    
    @classmethod
    def test_postgres_connection(cls, params: Optional[Dict] = None) -> tuple[bool, str]:
        """
        Test PostgreSQL connection with given or configured parameters.
        
        Args:
            params: Optional connection parameters, uses configured if None
            
        Returns:
            Tuple of (success, message)
        """
        try:
            import psycopg2
            
            if params is None:
                params = cls.get_postgres_params()
            
            conn = psycopg2.connect(
                host=params.get('host', 'localhost'),
                port=params.get('port', 5432),
                database=params['database'],
                user=params['user'],
                password=params['password'],
                connect_timeout=5
            )
            conn.close()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    @classmethod
    def create_sample_config(cls) -> bool:
        """Create a sample configuration file with defaults"""
        return cls.save_config(cls._get_default_config())
