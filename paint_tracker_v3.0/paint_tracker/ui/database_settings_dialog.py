"""
Database Settings Dialog
Allows users to configure database type and connection settings.

Author: Christopher Lajoie
CS 499 Enhancement Three: Database Enhancement
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QGroupBox,
    QSpinBox, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt
from paint_tracker.config.database_config import DatabaseConfig


class DatabaseSettingsDialog(QDialog):
    """Dialog for configuring database connection settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Settings")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout()
        
        # Database type selection
        type_group = QGroupBox("Database Type")
        type_layout = QVBoxLayout()
        
        self.db_type_group = QButtonGroup(self)
        self.sqlite_radio = QRadioButton("SQLite (Single User - Local File)")
        self.postgres_radio = QRadioButton("PostgreSQL (Multi-User - Network)")
        
        self.db_type_group.addButton(self.sqlite_radio, 1)
        self.db_type_group.addButton(self.postgres_radio, 2)
        
        type_layout.addWidget(self.sqlite_radio)
        type_layout.addWidget(self.postgres_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # SQLite settings
        self.sqlite_group = QGroupBox("SQLite Settings")
        sqlite_layout = QFormLayout()
        self.sqlite_path_edit = QLineEdit()
        sqlite_layout.addRow("Database File:", self.sqlite_path_edit)
        
        sqlite_browse_layout = QHBoxLayout()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_sqlite_path)
        sqlite_browse_layout.addStretch()
        sqlite_browse_layout.addWidget(browse_btn)
        sqlite_layout.addRow("", sqlite_browse_layout)
        
        self.sqlite_group.setLayout(sqlite_layout)
        layout.addWidget(self.sqlite_group)
        
        # PostgreSQL settings
        self.postgres_group = QGroupBox("PostgreSQL Settings")
        postgres_layout = QFormLayout()
        
        self.pg_host_edit = QLineEdit()
        self.pg_port_spin = QSpinBox()
        self.pg_port_spin.setRange(1, 65535)
        self.pg_port_spin.setValue(5432)
        self.pg_database_edit = QLineEdit()
        self.pg_user_edit = QLineEdit()
        self.pg_password_edit = QLineEdit()
        self.pg_password_edit.setEchoMode(QLineEdit.Password)
        
        postgres_layout.addRow("Host:", self.pg_host_edit)
        postgres_layout.addRow("Port:", self.pg_port_spin)
        postgres_layout.addRow("Database:", self.pg_database_edit)
        postgres_layout.addRow("Username:", self.pg_user_edit)
        postgres_layout.addRow("Password:", self.pg_password_edit)
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_postgres_connection)
        postgres_layout.addRow("", test_btn)
        
        self.postgres_group.setLayout(postgres_layout)
        layout.addWidget(self.postgres_group)
        
        # Connect signals
        self.sqlite_radio.toggled.connect(self.on_db_type_changed)
        self.postgres_radio.toggled.connect(self.on_db_type_changed)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Info label
        info_label = QLabel(
            "Note: Changing database type requires restarting the application.\n"
            "Make sure to backup your data before switching databases."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def load_current_settings(self):
        """Load current database settings"""
        db_type = DatabaseConfig.get_database_type()
        
        if db_type == "sqlite":
            self.sqlite_radio.setChecked(True)
            self.sqlite_path_edit.setText(DatabaseConfig.get_sqlite_path())
        else:
            self.postgres_radio.setChecked(True)
            params = DatabaseConfig.get_postgres_params()
            self.pg_host_edit.setText(params.get("host", "localhost"))
            self.pg_port_spin.setValue(params.get("port", 5432))
            self.pg_database_edit.setText(params.get("database", "paint_tracker"))
            self.pg_user_edit.setText(params.get("user", "paint_user"))
            self.pg_password_edit.setText(params.get("password", ""))
        
        self.on_db_type_changed()
    
    def on_db_type_changed(self):
        """Enable/disable settings based on database type"""
        is_sqlite = self.sqlite_radio.isChecked()
        self.sqlite_group.setEnabled(is_sqlite)
        self.postgres_group.setEnabled(not is_sqlite)
    
    def browse_sqlite_path(self):
        """Browse for SQLite database file"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database File",
            self.sqlite_path_edit.text(),
            "Database Files (*.db);;All Files (*)"
        )
        if file_path:
            self.sqlite_path_edit.setText(file_path)
    
    def test_postgres_connection(self):
        """Test PostgreSQL connection with current settings"""
        params = {
            "host": self.pg_host_edit.text(),
            "port": self.pg_port_spin.value(),
            "database": self.pg_database_edit.text(),
            "user": self.pg_user_edit.text(),
            "password": self.pg_password_edit.text()
        }
        
        success, message = DatabaseConfig.test_postgres_connection(params)
        
        if success:
            QMessageBox.information(self, "Connection Test", "✅ " + message)
        else:
            QMessageBox.warning(self, "Connection Test", "❌ " + message)
    
    def save_settings(self):
        """Save database settings"""
        if self.sqlite_radio.isChecked():
            # Save SQLite settings
            config = DatabaseConfig.load_config()
            config["database_type"] = "sqlite"
            config["sqlite"] = {"path": self.sqlite_path_edit.text()}
            success = DatabaseConfig.save_config(config)
            
            if success:
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Database settings saved successfully.\n"
                    "Please restart the application for changes to take effect."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save settings.")
        
        else:
            # Validate PostgreSQL fields
            if not all([
                self.pg_host_edit.text(),
                self.pg_database_edit.text(),
                self.pg_user_edit.text()
            ]):
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Please fill in all required PostgreSQL fields."
                )
                return
            
            # Save PostgreSQL settings
            success = DatabaseConfig.set_postgres_params(
                self.pg_host_edit.text(),
                self.pg_port_spin.value(),
                self.pg_database_edit.text(),
                self.pg_user_edit.text(),
                self.pg_password_edit.text()
            )
            
            if success:
                DatabaseConfig.set_database_type("postgresql")
                
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Database settings saved successfully.\n"
                    "Please restart the application for changes to take effect."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save settings.")
