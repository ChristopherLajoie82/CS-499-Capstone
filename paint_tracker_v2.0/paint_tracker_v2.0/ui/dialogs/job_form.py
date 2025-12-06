"""
Job Form Dialog with enhanced dropdowns for Paint Tracking System
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QFormLayout,
    QDialogButtonBox, QMessageBox, QInputDialog, QGroupBox, QRadioButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator, QDoubleValidator
from typing import Optional

from paint_tracker.config import SettingsManager
from paint_tracker.core import PaintCalculatorService

class JobFormDialog(QDialog):
    """Dialog for creating/editing paint mix entries with dropdowns"""

    job_saved = Signal()  # Signal emitted when job is saved

    def __init__(self, job_service, job_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.job_data = job_data
        self.is_edit_mode = job_data is not None and 'id' in job_data
        self.settings_manager = SettingsManager()
        self.calculator_service = PaintCalculatorService()
        self.calculated_components = None

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
        self.job_number_edit.setValidator(QIntValidator(0, 999999999, self))
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

        # Paint Code
        self.paint_code_edit = QLineEdit()
        form_layout.addRow("Paint Code:*", self.paint_code_edit)

        # Paint Version Dropdown
        self.paint_version_combo = QComboBox()
        self.paint_version_combo.setEditable(True)
        self.paint_version_combo.setValidator(QDoubleValidator(0.0, 99.9, 1, self))
        self.paint_version_combo.addItems(self.settings_manager.get_paint_versions())
        self.paint_version_combo.setCurrentText("1.0")
        form_layout.addRow("Paint Version:*", self.paint_version_combo)

        # Color Name
        self.color_name_edit = QLineEdit()
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

        self.components_display.setText(display_text)

       

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

    def add_operator(self):
        """Add a new operator to the mixed_by dropdown list"""
        text, ok = QInputDialog.getText(
            self, "Add Operator",
            "Enter operator name:"
        )
        if ok and text:
            # Capitalize to prevent duplicates
            text = text.strip().upper()
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
            'mixed_by': self.mixed_by_combo.currentText().strip().upper(),
            'notes': self.notes_edit.toPlainText().strip(),
            'job_type': self.get_selected_job_type(),
        }

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

        if not job_data['mixed_by']:
            QMessageBox.critical(self, "Error", "Mixed By is required")
            return

        if self.is_edit_mode:
            success, message = self.job_service.update_job(
                self.job_data['id'], job_data)
        else:
            success, message = self.job_service.create_job(job_data)

        if success:
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
