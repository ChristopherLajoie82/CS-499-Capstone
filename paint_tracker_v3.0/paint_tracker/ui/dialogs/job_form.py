"""
Job Form Dialog with enhanced dropdowns for Paint Tracking System
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QFormLayout,
    QDialogButtonBox, QMessageBox, QInputDialog, QGroupBox, QRadioButton, QCompleter
)
from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator, QRegularExpressionValidator
from typing import Optional

from paint_tracker.config import SettingsManager
from paint_tracker.core import PaintCalculatorService

class JobFormDialog(QDialog):
    """Dialog for creating/editing paint mix entries with dropdowns"""
    
    job_saved = Signal()  # Signal emitted when job is saved
    
    def __init__(self, job_service, job_data: Optional[dict] = None, current_username: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.job_data = job_data
        self.current_username = current_username
        self.is_edit_mode = job_data is not None and 'id' in job_data
        self.settings_manager = SettingsManager()
        self.calculator_service = PaintCalculatorService()  # Paint mix calculator
        self.calculated_components = None  # Store calculated component amounts
        
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
        
        # Job Number (integers only)
        self.job_number_edit = QLineEdit()
        self.job_number_edit.setValidator(QIntValidator(0, 999999999, self))  # Only whole numbers
        self.job_number_edit.setPlaceholderText("Enter job number (numbers only)")
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
        
        # Paint Code with auto-complete
        self.paint_code_edit = QLineEdit()
        form_layout.addRow("Paint Code:*", self.paint_code_edit)
        
        # Paint Version Dropdown
        self.paint_version_combo = QComboBox()
        self.paint_version_combo.setEditable(True)
        self.paint_version_combo.setValidator(QDoubleValidator(0.0, 99.9, 1, self))
        self.paint_version_combo.addItems(self.settings_manager.get_paint_versions())
        self.paint_version_combo.setCurrentText("1.0")
        form_layout.addRow("Paint Version:*", self.paint_version_combo)
        
        # Color Name with auto-complete
        self.color_name_edit = QLineEdit()
        # Set up auto-complete for color names (will be set up along with paint codes)
        form_layout.addRow("Color Name:", self.color_name_edit)
        
        # Job Type Selection
        job_type_group = QGroupBox("Job Type (for mix calculations)")
        job_type_layout = QHBoxLayout()
        
        self.interior_radio = QRadioButton("Interior (3:1:3 ratio)")
        self.exterior_radio = QRadioButton("Exterior (3:1:1 ratio)")
        self.interior_radio.setChecked(True)  # Default to interior
        
        # Connect radio buttons to recalculate when changed
        self.interior_radio.toggled.connect(self.on_job_type_changed)
        self.exterior_radio.toggled.connect(self.on_job_type_changed)
        
        job_type_layout.addWidget(self.interior_radio)
        job_type_layout.addWidget(self.exterior_radio)
        job_type_group.setLayout(job_type_layout)
        form_layout.addRow(job_type_group)
        
        # Mixed Amount with Calculator Button
        mixed_amount_layout = QHBoxLayout()
        self.mixed_amount_edit = QLineEdit()
        self.mixed_amount_edit.setValidator(QDoubleValidator(0.1, 99999.9, 1, self))
        self.mixed_amount_edit.setPlaceholderText("Enter total weight in grams")
        self.mixed_amount_edit.textChanged.connect(self.on_amount_changed)
        mixed_amount_layout.addWidget(self.mixed_amount_edit)
        
        calc_btn = QPushButton("Calculate Mix")
        calc_btn.setToolTip("Calculate component amounts based on job type")
        calc_btn.clicked.connect(self.calculate_and_show_mix)
        mixed_amount_layout.addWidget(calc_btn)
        
        form_layout.addRow("Mixed Amount:*", mixed_amount_layout)
        
        # Matte Clear Option
        from PySide6.QtWidgets import QCheckBox
        self.matte_checkbox = QCheckBox("Add Matte Clear (32% ratio)")
        self.matte_checkbox.setToolTip("Calculate matte clear to add (32% of paint amount)")
        self.matte_checkbox.stateChanged.connect(self.on_matte_changed)
        form_layout.addRow("", self.matte_checkbox)
        
        # Calculated Components Display (read-only labels)
        self.components_display = QLabel("")
        self.components_display.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-family: monospace;
            }
        """)
        self.components_display.setWordWrap(True)
        form_layout.addRow("Calculated Mix:", self.components_display)
        
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
        
        # Set up auto-complete for paint codes and color names after all fields are created
        self.setup_autocomplete()
        
        self.setLayout(layout)
    
    def setup_autocomplete(self):
        """Set up auto-complete for paint codes and color names based on existing data in database"""
        try:
            # Get all unique paint codes and color names from the database
            all_jobs = self.job_service.repository.get_all_jobs()
            paint_codes = set()
            color_names = set()
            
            for job in all_jobs:
                if job.get('paint_code'):
                    paint_codes.add(job['paint_code'])
                if job.get('color_name'):
                    color_names.add(job['color_name'])
            
            # Set up paint code completer
            if paint_codes:
                paint_code_completer = QCompleter(sorted(list(paint_codes)))
                paint_code_completer.setCaseSensitivity(Qt.CaseInsensitive)
                paint_code_completer.setCompletionMode(QCompleter.PopupCompletion)
                self.paint_code_edit.setCompleter(paint_code_completer)
            
            # Set up color name completer
            if color_names:
                color_name_completer = QCompleter(sorted(list(color_names)))
                color_name_completer.setCaseSensitivity(Qt.CaseInsensitive)
                color_name_completer.setCompletionMode(QCompleter.PopupCompletion)
                self.color_name_edit.setCompleter(color_name_completer)
                
        except Exception as e:
            # If there's an error, just skip auto-complete setup
            pass
        
        # Focus on first field
        if not self.job_number_edit.text():
            self.job_number_edit.setFocus()
    
    def get_selected_job_type(self) -> str:
        """Get the currently selected job type"""
        return 'interior' if self.interior_radio.isChecked() else 'exterior'
    
    def on_job_type_changed(self):
        """Handle job type radio button changes - recalculate if amount is entered"""
        if self.mixed_amount_edit.text().strip():
            self.calculate_and_show_mix()
    
    def on_amount_changed(self):
        """Handle amount field changes - clear calculated display if empty"""
        if not self.mixed_amount_edit.text().strip():
            self.components_display.setText("")
            self.calculated_components = None
    
    def on_matte_changed(self):
        """Handle matte checkbox changes - recalculate if amount is entered"""
        if self.mixed_amount_edit.text().strip():
            self.calculate_and_show_mix()
    
    def calculate_and_show_mix(self):
        """Calculate component amounts using the algorithm"""
        amount_text = self.mixed_amount_edit.text().strip()
        
        if not amount_text:
            QMessageBox.warning(self, "Missing Information", "Please enter a total amount first")
            return
        
        try:
            total_amount = float(amount_text)
            if total_amount <= 0:
                QMessageBox.warning(self, "Invalid Amount", "Total amount must be greater than 0")
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number for total amount")
            return
        
        job_type = self.get_selected_job_type()
        result = self.calculator_service.calculate_mix_from_job_type(job_type, total_amount)
        
        if not result['success']:
            QMessageBox.critical(self, "Calculation Error", result.get('error', 'Unknown error'))
            return
        
        self.calculated_components = result['components']
        
        ratio = result['ratio']
        components = result['components']
        
        display_text = f"<b>Ratio: {ratio}</b><br><br>"
        
        for component, amount in components.items():
            display_text += f"{component.capitalize()}: <b>{amount:.1f}g</b><br>"
        
        display_text += f"<br>Total: <b>{total_amount:.1f}g</b>"
        
        # Add matte clear calculation if checkbox is checked
        if self.matte_checkbox.isChecked():
            matte_clear_amount = total_amount * 0.32
            display_text += f"<br><br><b>For Matte Finish:</b><br>"
            display_text += f"Add Matte Clear: <b>{matte_clear_amount:.1f}g</b><br>"
            display_text += f"Final Total: <b>{(total_amount + matte_clear_amount):.1f}g</b>"
        
        self.components_display.setText(display_text)
        
        # Popup removed - component breakdown already visible in the form
    
    def add_manufacturer(self):
        """Add a new manufacturer to the dropdown list"""
        text, ok = QInputDialog.getText(
            self, "Add Manufacturer", 
            "Enter new manufacturer name:"
        )
        if ok and text:
            # Capitalize to prevent duplicates
            text = text.strip().upper()
            if self.settings_manager.add_manufacturer(text):
                self.manufacturer_combo.clear()
                self.manufacturer_combo.addItems(self.settings_manager.get_manufacturers())
                self.manufacturer_combo.setCurrentText(text)
                QMessageBox.information(self, "Success", f"Added '{text}' to manufacturers list")
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
            if 'notes' in self.job_data:
                self.notes_edit.setText(self.job_data.get('notes', ''))
            
            # Set job type if available
            if 'job_type' in self.job_data and self.job_data['job_type']:
                if self.job_data['job_type'].lower() == 'exterior':
                    self.exterior_radio.setChecked(True)
                else:
                    self.interior_radio.setChecked(True)
            
            # Display calculated components if available
            if all(k in self.job_data for k in ['paint_amount', 'catalyst_amount', 'third_component_amount']):
                if self.job_data['paint_amount']:  # Check if values exist
                    job_type = self.job_data.get('job_type', 'interior')
                    third_name = self.job_data.get('third_component_name', 'additive')
                    
                    self.calculated_components = {
                        'paint': self.job_data['paint_amount'],
                        'catalyst': self.job_data['catalyst_amount'],
                        third_name: self.job_data['third_component_amount']
                    }
                    
                    ratio_info = self.calculator_service.get_ratio_info(job_type)
                    ratio = ratio_info.get('ratio', '3:1:3')
                    
                    display_text = f"<b>Ratio: {ratio}</b><br><br>"
                    display_text += f"Paint: <b>{self.job_data['paint_amount']:.1f}g</b><br>"
                    display_text += f"Catalyst: <b>{self.job_data['catalyst_amount']:.1f}g</b><br>"
                    display_text += f"{third_name.capitalize()}: <b>{self.job_data['third_component_amount']:.1f}g</b><br>"
                    display_text += f"<br>Total: <b>{self.job_data['mixed_amount']:.1f}g</b>"
                    
                    self.components_display.setText(display_text)
    
    def save_job(self):
        """Save or update the job"""
        # Check if user has entered an amount but hasn't calculated the mix
        has_amount = bool(self.mixed_amount_edit.text().strip())
        has_job_type = self.interior_radio.isChecked() or self.exterior_radio.isChecked()
        has_calculated = bool(self.calculated_components)
        
        # Reminder if amount entered but no job type selected or mix not calculated
        if has_amount and has_job_type and not has_calculated:
            reply = QMessageBox.question(
                self,
                "Mix Not Calculated",
                "You selected a job type but haven't calculated the component mix.\n\n"
                "Do you want to save without component breakdown?\n\n"
                "Click 'No' to go back and click 'Calculate Mix'.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default to No
            )
            if reply == QMessageBox.No:
                return
        
        # Collect form data and capitalize text fields to prevent duplicates
        job_data = {
            'job_number': self.job_number_edit.text().strip().upper(),
            'manufacturer': self.manufacturer_combo.currentText().strip().upper(),
            'paint_code': self.paint_code_edit.text().strip().upper(),
            'paint_version': self.paint_version_combo.currentText().strip(),
            'color_name': self.color_name_edit.text().strip().upper(),
            'mixed_amount': self.mixed_amount_edit.text().strip(),
            'mixed_by': (self.current_username or '').upper(),
            'notes': self.notes_edit.toPlainText().strip(),
            'job_type': self.get_selected_job_type(),
        }
        
        # Add matte clear info to notes if checkbox is checked
        if self.matte_checkbox.isChecked() and job_data['mixed_amount']:
            try:
                amount = float(job_data['mixed_amount'])
                matte_amount = amount * 0.32
                total_with_matte = amount + matte_amount
                matte_note = f"[MATTE FINISH] Paint: {amount:.1f}g + Matte Clear: {matte_amount:.1f}g = Total: {total_with_matte:.1f}g"
                if job_data['notes']:
                    job_data['notes'] = f"{matte_note}\n{job_data['notes']}"
                else:
                    job_data['notes'] = matte_note
                # Update the mixed_amount to include the matte clear
                job_data['mixed_amount'] = str(total_with_matte)
            except ValueError:
                pass  # If amount is not a valid number, skip matte calculation
        
        if self.calculated_components:
            job_data['paint_amount'] = self.calculated_components.get('paint')
            job_data['catalyst_amount'] = self.calculated_components.get('catalyst')
            
            # Determine third component name and amount based on job type
            if 'additive' in self.calculated_components:
                job_data['third_component_name'] = 'additive'
                job_data['third_component_amount'] = self.calculated_components.get('additive')
            elif 'reducer' in self.calculated_components:
                job_data['third_component_name'] = 'reducer'
                job_data['third_component_amount'] = self.calculated_components.get('reducer')
        
        if not job_data['job_number']:
            QMessageBox.critical(self, "Error", "Job Number is required")
            return
        
        if not job_data['manufacturer']:
            QMessageBox.critical(self, "Error", "Manufacturer is required")
            return
        
        if not job_data['paint_code']:
            QMessageBox.critical(self, "Error", "Paint Code is required")
            return
        
        if not job_data['mixed_amount']:
            QMessageBox.critical(self, "Error", "Mixed Amount is required")
            return
        
        if self.is_edit_mode:
            success, message = self.job_service.update_job(
                self.job_data['id'], job_data)
        else:
            success, message = self.job_service.create_job(job_data)
        
        if success:
            # Save any new dropdown values that were typed in
            if job_data['manufacturer'] not in self.settings_manager.get_manufacturers():
                self.settings_manager.add_manufacturer(job_data['manufacturer'])
            
            if job_data['paint_version'] not in self.settings_manager.get_paint_versions():
                self.settings_manager.add_paint_version(job_data['paint_version'])
            
            QMessageBox.information(self, "Success", message)
            self.job_saved.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
