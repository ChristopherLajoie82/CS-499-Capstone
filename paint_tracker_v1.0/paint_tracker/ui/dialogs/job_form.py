"""
Job Form Dialog with enhanced dropdowns for Paint Tracking System
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QFormLayout,
    QDialogButtonBox, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional, Dict

from paint_tracker.config import SettingsManager

class JobFormDialog(QDialog):
    """Dialog for creating/editing paint mix entries with dropdowns"""
    
    job_saved = Signal()  # Signal emitted when job is saved
    
    def __init__(self, job_service, job_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.job_data = job_data
        self.is_edit_mode = job_data is not None and 'id' in job_data
        self.settings_manager = SettingsManager()
        
        self.setup_ui()
        if self.is_edit_mode:
            self.populate_form()
    
    def setup_ui(self):
        """Setup the dialog UI with dropdown menus"""
        self.setWindowTitle("Edit Mix Entry" if self.is_edit_mode else "Create New Mix Entry")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Edit Mix Details" if self.is_edit_mode else "Create New Mix Entry")
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Job Number
        self.job_number_edit = QLineEdit()
        if self.is_edit_mode and 'job_number' in self.job_data:
            self.job_number_edit.setText(self.job_data['job_number'])
        form_layout.addRow("Job Number:*", self.job_number_edit)
        
        # Manufacturer Dropdown with Add Option
        manufacturer_layout = QHBoxLayout()
        self.manufacturer_combo = QComboBox()
        self.manufacturer_combo.setEditable(True)
        self.manufacturer_combo.addItems(self.settings_manager.get_manufacturers())
        manufacturer_layout.addWidget(self.manufacturer_combo)
        
        add_manufacturer_btn = QPushButton("+")
        add_manufacturer_btn.setMaximumWidth(30)
        add_manufacturer_btn.setToolTip("Add new manufacturer to list")
        add_manufacturer_btn.clicked.connect(self.add_manufacturer)
        manufacturer_layout.addWidget(add_manufacturer_btn)
        
        form_layout.addRow("Manufacturer:*", manufacturer_layout)
        
        # Paint Code
        self.paint_code_edit = QLineEdit()
        form_layout.addRow("Paint Code:*", self.paint_code_edit)
        
        # Paint Version Dropdown
        self.paint_version_combo = QComboBox()
        self.paint_version_combo.setEditable(True)
        self.paint_version_combo.addItems(self.settings_manager.get_paint_versions())
        self.paint_version_combo.setCurrentText("1.0")
        form_layout.addRow("Paint Version:*", self.paint_version_combo)
        
        # Color Name
        self.color_name_edit = QLineEdit()
        form_layout.addRow("Color Name:", self.color_name_edit)
        
        # Mixed Amount
        self.mixed_amount_edit = QLineEdit()
        self.mixed_amount_edit.setPlaceholderText("Enter amount in grams")
        form_layout.addRow("Amount Mixed:*", self.mixed_amount_edit)
        
        # Mixed By Dropdown with Add Option
        mixed_by_layout = QHBoxLayout()
        self.mixed_by_combo = QComboBox()
        self.mixed_by_combo.setEditable(True)
        self.mixed_by_combo.addItems(self.settings_manager.get_operators())
        mixed_by_layout.addWidget(self.mixed_by_combo)
        
        add_operator_btn = QPushButton("+")
        add_operator_btn.setMaximumWidth(30)
        add_operator_btn.setToolTip("Add new operator to list")
        add_operator_btn.clicked.connect(self.add_operator)
        mixed_by_layout.addWidget(add_operator_btn)
        
        form_layout.addRow("Mixed By:*", mixed_by_layout)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Enter any notes about this mix...")
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Required fields note
        required_label = QLabel("* Required fields")
        required_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(required_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        save_btn = button_box.addButton(
            "Update" if self.is_edit_mode else "Save", 
            QDialogButtonBox.AcceptRole
        )
        save_btn.clicked.connect(self.save_job)
        
        cancel_btn = button_box.addButton("Cancel", QDialogButtonBox.RejectRole)
        cancel_btn.clicked.connect(self.reject)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Focus on first field
        if not self.job_number_edit.text():
            self.job_number_edit.setFocus()
    
    def add_manufacturer(self):
        """Add a new manufacturer to the dropdown list"""
        text, ok = QInputDialog.getText(
            self, "Add Manufacturer", 
            "Enter new manufacturer name:"
        )
        if ok and text:
            if self.settings_manager.add_manufacturer(text):
                self.manufacturer_combo.clear()
                self.manufacturer_combo.addItems(self.settings_manager.get_manufacturers())
                self.manufacturer_combo.setCurrentText(text)
                QMessageBox.information(self, "Success", f"Added '{text}' to manufacturers list")
            else:
                QMessageBox.warning(self, "Warning", f"'{text}' already exists in the list")
    
    def add_operator(self):
        """Add a new operator to the mixed_by dropdown list"""
        text, ok = QInputDialog.getText(
            self, "Add Operator", 
            "Enter operator name:"
        )
        if ok and text:
            if self.settings_manager.add_operator(text):
                self.mixed_by_combo.clear()
                self.mixed_by_combo.addItems(self.settings_manager.get_operators())
                self.mixed_by_combo.setCurrentText(text)
                QMessageBox.information(self, "Success", f"Added '{text}' to operators list")
            else:
                QMessageBox.warning(self, "Warning", f"'{text}' already exists in the list")
    
    def populate_form(self):
        """Populate form with existing job data"""
        if self.job_data:
            self.job_number_edit.setText(self.job_data.get('job_number', ''))
            self.manufacturer_combo.setCurrentText(
                self.job_data.get('manufacturer', ''))
            self.paint_code_edit.setText(self.job_data.get('paint_code', ''))
            self.paint_version_combo.setCurrentText(
                self.job_data.get('paint_version', '1.0'))
            self.color_name_edit.setText(self.job_data.get('color_name', ''))
            self.mixed_amount_edit.setText(
                str(self.job_data.get('mixed_amount', '')))
            self.mixed_by_combo.setCurrentText(
                self.job_data.get('mixed_by', ''))
            if 'notes' in self.job_data:
                self.notes_edit.setText(self.job_data.get('notes', ''))
    
    def save_job(self):
        """Save or update the job"""
        # Collect form data
        job_data = {
            'job_number': self.job_number_edit.text().strip(),
            'manufacturer': self.manufacturer_combo.currentText().strip(),
            'paint_code': self.paint_code_edit.text().strip(),
            'paint_version': self.paint_version_combo.currentText().strip(),
            'color_name': self.color_name_edit.text().strip(),
            'mixed_amount': self.mixed_amount_edit.text().strip(),
            'mixed_by': self.mixed_by_combo.currentText().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }
        
        # Validate required fields
        if not job_data['job_number']:
            QMessageBox.critical(self, "Error", "Job Number is required")
            return
        
        if not job_data['manufacturer']:
            QMessageBox.critical(self, "Error", "Manufacturer is required")
            return
        
        if not job_data['paint_code']:
            QMessageBox.critical(self, "Error", "Paint Code is required")
            return
        
        if not job_data['mixed_by']:
            QMessageBox.critical(self, "Error", "Mixed By is required")
            return
        
        # Save to database
        if self.is_edit_mode:
            success, message = self.job_service.update_job(
                self.job_data['id'], job_data)
        else:
            success, message = self.job_service.create_job(job_data)
        
        if success:
            # Save any new dropdown values that were typed in
            if job_data['manufacturer'] not in self.settings_manager.get_manufacturers():
                self.settings_manager.add_manufacturer(job_data['manufacturer'])
            
            if job_data['mixed_by'] and job_data['mixed_by'] not in self.settings_manager.get_operators():
                self.settings_manager.add_operator(job_data['mixed_by'])
            
            if job_data['paint_version'] not in self.settings_manager.get_paint_versions():
                self.settings_manager.add_paint_version(job_data['paint_version'])
            
            QMessageBox.information(self, "Success", message)
            self.job_saved.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
