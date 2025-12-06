"""
Job Detail Dialog for Paint Tracking System
Shows all paint mixing history for a specific job number
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import List, Dict


class JobDetailDialog(QDialog):
    """Dialog to display all paint mixing entries for a specific job"""
    
    refresh_requested = Signal()  # Signal to refresh main dashboard
    
    def __init__(self, job_number: str, job_service, export_service, parent=None):
        super().__init__(parent)
        self.job_number = job_number
        self.job_service = job_service
        self.export_service = export_service
        self.job_entries = []
        
        self.setWindowTitle(f"Job Details - {job_number}")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
        self.load_job_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        # Job Number Title
        title_label = QLabel(f"Job Number: {self.job_number}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Action buttons
        add_color_btn = QPushButton("Add Color")
        add_color_btn.clicked.connect(self.add_new_color)
        header_layout.addWidget(add_color_btn)
        
        export_btn = QPushButton("Export Job")
        export_btn.clicked.connect(self.export_job_data)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Summary Section
        self.summary_group = QGroupBox("Job Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_label = QLabel()
        summary_layout.addWidget(self.summary_label)
        
        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)
        
        # Paint Mixing History Table
        history_group = QGroupBox("Paint Mixing History")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSortingEnabled(True)
        
        # Set columns
        columns = ['ID', 'Date Mixed', 'Color Name', 'Paint Code', 
                  'Version', 'Manufacturer', 'Amount', 'Mixed By', 'Notes']
        self.history_table.setColumnCount(len(columns))
        self.history_table.setHorizontalHeaderLabels(columns)
        
        # Hide ID column
        self.history_table.setColumnHidden(0, True)
        
        # Adjust column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # Set specific column widths
        self.history_table.setColumnWidth(1, 120)  # Date
        self.history_table.setColumnWidth(2, 150)  # Color
        self.history_table.setColumnWidth(3, 100)  # Paint Code
        self.history_table.setColumnWidth(4, 70)   # Version
        self.history_table.setColumnWidth(5, 120)  # Manufacturer
        self.history_table.setColumnWidth(6, 80)   # Amount
        self.history_table.setColumnWidth(7, 100)  # Mixed By
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Notes Section (for selected entry)
        self.notes_group = QGroupBox("Notes for Selected Entry")
        notes_layout = QVBoxLayout()
        
        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        self.notes_display.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_display)
        
        self.notes_group.setLayout(notes_layout)
        layout.addWidget(self.notes_group)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self.edit_selected)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
        delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(delete_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect table selection to show notes
        self.history_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_job_data(self):
        """Load all entries for this job number"""
        # Get all entries for this job
        self.job_entries = self.job_service.get_all_job_entries(self.job_number)
        
        # Clear table
        self.history_table.setRowCount(0)
        
        # Populate table
        total_amount = 0
        colors_used = set()
        
        for entry in self.job_entries:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # ID (hidden)
            self.history_table.setItem(row, 0, 
                QTableWidgetItem(str(entry['id'])))
            
            # Date Mixed
            date_str = entry.get('created_at', '')[:10] if entry.get('created_at') else ''
            self.history_table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Color Name
            color = entry.get('color_name', 'N/A')
            if color:
                colors_used.add(color)
            self.history_table.setItem(row, 2, QTableWidgetItem(color))
            
            # Paint Code
            self.history_table.setItem(row, 3, 
                QTableWidgetItem(entry.get('paint_code', '')))
            
            # Version
            self.history_table.setItem(row, 4, 
                QTableWidgetItem(entry.get('paint_version', '1.0')))
            
            # Manufacturer
            self.history_table.setItem(row, 5, 
                QTableWidgetItem(entry.get('manufacturer', '')))
            
            # Amount
            amount = entry.get('mixed_amount', 0)
            total_amount += float(amount)
            self.history_table.setItem(row, 6, 
                QTableWidgetItem(f"{amount} units"))
            
            # Mixed By
            self.history_table.setItem(row, 7, 
                QTableWidgetItem(entry.get('mixed_by', 'N/A')))
            
            # Notes (stored but not shown in table)
            notes_item = QTableWidgetItem(entry.get('notes', ''))
            notes_item.setData(Qt.UserRole, entry.get('notes', ''))
            self.history_table.setItem(row, 8, notes_item)
        
        # Update summary
        summary_text = f"""
        <b>Total Entries:</b> {len(self.job_entries)}<br>
        <b>Total Paint Mixed:</b> {total_amount:.2f} units<br>
        <b>Colors Used:</b> {', '.join(colors_used) if colors_used else 'N/A'}<br>
        <b>Average per Mix:</b> {(total_amount/len(self.job_entries)):.2f} units
        """ if self.job_entries else "<b>No entries found for this job</b>"
        
        self.summary_label.setText(summary_text)
    
    def on_selection_changed(self):
        """Update notes display when selection changes"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            notes_item = self.history_table.item(current_row, 8)
            if notes_item:
                notes = notes_item.data(Qt.UserRole)
                self.notes_display.setPlainText(notes if notes else "No notes for this entry")
        else:
            self.notes_display.clear()
    
    def add_new_color(self):
        """Add a new color entry for this job"""
        from paint_tracker.ui.dialogs import JobFormDialog
        
        # Pre-fill job number
        job_data = {'job_number': self.job_number}
        
        dialog = JobFormDialog(self.job_service, job_data=job_data, parent=self)
        dialog.job_saved.connect(self.load_job_data)
        dialog.job_saved.connect(self.refresh_requested.emit)
        
        # Make job number field read-only since we're adding to existing job
        dialog.job_number_edit.setEnabled(False)
        
        dialog.exec()
    
    def edit_selected(self):
        """Edit the selected entry"""
        current_row = self.history_table.currentRow()
        if current_row < 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Selection", 
                               "Please select an entry to edit")
            return
        
        # Get the selected entry data
        entry_id = int(self.history_table.item(current_row, 0).text())
        entry_data = next((e for e in self.job_entries if e['id'] == entry_id), None)
        
        if entry_data:
            from paint_tracker.ui.dialogs import JobFormDialog
            dialog = JobFormDialog(self.job_service, job_data=entry_data, parent=self)
            dialog.job_saved.connect(self.load_job_data)
            dialog.job_saved.connect(self.refresh_requested.emit)
            dialog.exec()
    
    def delete_selected(self):
        """Delete the selected entry"""
        current_row = self.history_table.currentRow()
        if current_row < 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Selection", 
                               "Please select an entry to delete")
            return
        
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    "Are you sure you want to delete this entry?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            entry_id = int(self.history_table.item(current_row, 0).text())
            success, message = self.job_service.delete_job(entry_id)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.load_job_data()
                self.refresh_requested.emit()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def export_job_data(self):
        """Export this job's data to CSV"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import csv
        
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Export Job {self.job_number}", 
            f"job_{self.job_number}.csv", "CSV Files (*.csv)")
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['date', 'color_name', 'paint_code', 'version', 
                                'manufacturer', 'amount', 'notes']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for entry in self.job_entries:
                        writer.writerow({
                            'date': entry.get('created_at', '')[:10],
                            'color_name': entry.get('color_name', ''),
                            'paint_code': entry.get('paint_code', ''),
                            'version': entry.get('paint_version', '1.0'),
                            'manufacturer': entry.get('manufacturer', ''),
                            'amount': entry.get('mixed_amount', ''),
                            'notes': entry.get('notes', '')
                        })
                
                QMessageBox.information(self, "Success", 
                                      f"Job data exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
