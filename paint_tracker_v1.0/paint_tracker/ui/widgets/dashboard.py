"""
Dashboard Widget for Paint Tracking System
Shows job information in the main table
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QRadioButton, QButtonGroup, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class DashboardWidget(QWidget):
    """Dashboard with job information display"""
    
    def __init__(self, job_service, export_service, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.export_service = export_service
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout()
        
        # Header Section
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Paint Tracking System - Job Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Statistics Box
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_layout)
        stats_group.setMaximumWidth(300)
        header_layout.addWidget(stats_group)
        
        layout.addLayout(header_layout)
        
        # Search Section
        search_layout = QHBoxLayout()
        
        # Search Filter Group
        filter_group = QGroupBox("Search Filter")
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by job number, color, paint code, or operator...")
        self.search_edit.returnPressed.connect(self.perform_search)
        filter_layout.addWidget(self.search_edit)
        
        # Filter options
        self.filter_all = QRadioButton("All Jobs")
        self.filter_all.setChecked(True)
        self.filter_recent = QRadioButton("Last 30 Days")
        
        self.filter_group = QButtonGroup()
        self.filter_group.addButton(self.filter_all)
        self.filter_group.addButton(self.filter_recent)
        
        filter_layout.addWidget(self.filter_all)
        filter_layout.addWidget(self.filter_recent)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        filter_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        filter_layout.addWidget(clear_btn)
        
        filter_group.setLayout(filter_layout)
        search_layout.addWidget(filter_group)
        
        layout.addLayout(search_layout)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        new_job_btn = QPushButton("New Job")
        new_job_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        new_job_btn.clicked.connect(self.create_new_job)
        button_layout.addWidget(new_job_btn)
        
        view_history_btn = QPushButton("View Job History")
        view_history_btn.clicked.connect(self.view_job_history)
        button_layout.addWidget(view_history_btn)
        
        delete_btn = QPushButton("Delete Job")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
        """)
        delete_btn.clicked.connect(self.delete_job)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        report_btn = QPushButton("Generate Report")
        report_btn.clicked.connect(self.generate_report)
        button_layout.addWidget(report_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Jobs Table setup
        self.jobs_table = QTableWidget()
        self.jobs_table.setAlternatingRowColors(True)
        self.jobs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.jobs_table.setSortingEnabled(True)
        
        # All the columns we want to show
        columns = [
            'ID',           # Hidden
            'Job Number',
            'Manufacturer',
            'Paint Code',
            'Version',
            'Color Name',
            'Amount (g)',
            'Mixed By',
            'Date Mixed',
            'Last Updated',
            'Notes'
        ]
        
        self.jobs_table.setColumnCount(len(columns))
        self.jobs_table.setHorizontalHeaderLabels(columns)
        
        # Hide ID column
        self.jobs_table.setColumnHidden(0, True)
        
        # Set column widths for better visibility
        header = self.jobs_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Set specific widths
        self.jobs_table.setColumnWidth(1, 100)   # Job Number
        self.jobs_table.setColumnWidth(2, 120)   # Manufacturer
        self.jobs_table.setColumnWidth(3, 100)   # Paint Code
        self.jobs_table.setColumnWidth(4, 70)    # Version
        self.jobs_table.setColumnWidth(5, 150)   # Color Name
        self.jobs_table.setColumnWidth(6, 80)    # Amount
        self.jobs_table.setColumnWidth(7, 100)   # Mixed By
        self.jobs_table.setColumnWidth(8, 100)   # Date Mixed
        self.jobs_table.setColumnWidth(9, 100)   # Last Updated
        self.jobs_table.setColumnWidth(10, 200)  # Notes (stretches)
        
        # Make notes column stretch to fill
        header.setStretchLastSection(True)
        
        # Double-click to view details
        self.jobs_table.itemDoubleClicked.connect(self.view_job_history)
        
        layout.addWidget(self.jobs_table)
        
        self.setLayout(layout)
    
    def refresh_data(self):
        """Refresh the dashboard with latest data"""
        # Get all jobs with full details
        jobs = self.job_service.repository.get_all_jobs()
        
        # Clear table
        self.jobs_table.setRowCount(0)
        
        # Fill in the table rows
        for job in jobs:
            row = self.jobs_table.rowCount()
            self.jobs_table.insertRow(row)
            
            # ID (hidden)
            self.jobs_table.setItem(row, 0, 
                QTableWidgetItem(str(job.get('id', ''))))
            
            # Job Number
            self.jobs_table.setItem(row, 1, 
                QTableWidgetItem(job.get('job_number', '')))
            
            # Manufacturer
            self.jobs_table.setItem(row, 2, 
                QTableWidgetItem(job.get('manufacturer', '')))
            
            # Paint Code
            self.jobs_table.setItem(row, 3, 
                QTableWidgetItem(job.get('paint_code', '')))
            
            # Version
            version = job.get('paint_version', '1.0')
            version_item = QTableWidgetItem(version)
            version_item.setTextAlignment(Qt.AlignCenter)
            self.jobs_table.setItem(row, 4, version_item)
            
            # Color Name
            self.jobs_table.setItem(row, 5, 
                QTableWidgetItem(job.get('color_name', 'N/A')))
            
            # Amount
            amount = job.get('mixed_amount', 0)
            amount_item = QTableWidgetItem(f"{amount:.1f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.jobs_table.setItem(row, 6, amount_item)
            
            # Mixed By
            mixed_by = job.get('mixed_by', 'Unknown')
            self.jobs_table.setItem(row, 7, 
                QTableWidgetItem(mixed_by if mixed_by else 'Unknown'))
            
            # Date Mixed
            created = job.get('created_at', '')
            if created:
                # Format date nicely
                try:
                    date_str = created[:16].replace('T', ' ')
                except:
                    date_str = created
            else:
                date_str = 'N/A'
            self.jobs_table.setItem(row, 8, QTableWidgetItem(date_str))
            
            # Last Updated
            updated = job.get('updated_at', '')
            if updated:
                try:
                    update_str = updated[:10]
                except:
                    update_str = updated
            else:
                update_str = 'N/A'
            self.jobs_table.setItem(row, 9, QTableWidgetItem(update_str))
            
            # Notes (truncate if too long)
            notes = job.get('notes', '')
            if len(notes) > 50:
                notes = notes[:47] + '...'
            self.jobs_table.setItem(row, 10, QTableWidgetItem(notes))
        
        # Update statistics
        self.update_statistics()
    
    def update_statistics(self):
        """Update the statistics display"""
        stats = self.job_service.get_statistics()
        
        stats_text = f"""
        <b>Total Jobs:</b> {stats.get('total_jobs', 0)}<br>
        <b>Recent Jobs:</b> {stats.get('recent_jobs', 0)}<br>
        <b>Total Paint Mixed:</b> {stats.get('total_paint', 0):.1f} g<br>
        <b>Average per Job:</b> {stats.get('average_paint_per_job', 0):.1f} g
        """
        
        self.stats_label.setText(stats_text.strip())
    
    def perform_search(self):
        """Perform search based on filter criteria"""
        search_term = self.search_edit.text()
        filter_type = "recent" if self.filter_recent.isChecked() else "all"
        
        if not search_term:
            self.refresh_data()
            return
        
        # Get filtered results
        results = self.job_service.search_jobs(search_term, filter_type)
        
        # Clear and populate table
        self.jobs_table.setRowCount(0)
        
        for job in results:
            row = self.jobs_table.rowCount()
            self.jobs_table.insertRow(row)
            
            # Populate all columns as in refresh_data
            self.jobs_table.setItem(row, 0, QTableWidgetItem(str(job.get('id', ''))))
            self.jobs_table.setItem(row, 1, QTableWidgetItem(job.get('job_number', '')))
            self.jobs_table.setItem(row, 2, QTableWidgetItem(job.get('manufacturer', '')))
            self.jobs_table.setItem(row, 3, QTableWidgetItem(job.get('paint_code', '')))
            self.jobs_table.setItem(row, 4, QTableWidgetItem(job.get('paint_version', '1.0')))
            self.jobs_table.setItem(row, 5, QTableWidgetItem(job.get('color_name', 'N/A')))
            
            amount = job.get('mixed_amount', 0)
            amount_item = QTableWidgetItem(f"{amount:.1f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.jobs_table.setItem(row, 6, amount_item)
            
            self.jobs_table.setItem(row, 7, QTableWidgetItem(job.get('mixed_by', 'Unknown')))
            
            created = job.get('created_at', '')[:16].replace('T', ' ') if job.get('created_at') else 'N/A'
            self.jobs_table.setItem(row, 8, QTableWidgetItem(created))
            
            updated = job.get('updated_at', '')[:10] if job.get('updated_at') else 'N/A'
            self.jobs_table.setItem(row, 9, QTableWidgetItem(updated))
            
            notes = job.get('notes', '')
            if len(notes) > 50:
                notes = notes[:47] + '...'
            self.jobs_table.setItem(row, 10, QTableWidgetItem(notes))
    
    def clear_search(self):
        """Clear search and refresh"""
        self.search_edit.clear()
        self.filter_all.setChecked(True)
        self.refresh_data()
    
    def create_new_job(self):
        """Open dialog to create new job"""
        from paint_tracker.ui.dialogs import JobFormDialog
        
        dialog = JobFormDialog(self.job_service, parent=self)
        dialog.job_saved.connect(self.refresh_data)
        dialog.exec()
    
    def view_job_history(self):
        """View detailed history for selected job"""
        current_row = self.jobs_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", 
                               "Please select a job to view details")
            return
        
        job_number = self.jobs_table.item(current_row, 1).text()
        
        from paint_tracker.ui.dialogs import JobDetailDialog
        from paint_tracker.config import SettingsManager
        
        dialog = JobDetailDialog(job_number, self.job_service, 
                               self.export_service, parent=self)
        dialog.refresh_requested.connect(self.refresh_data)
        dialog.exec()
    
    def delete_job(self):
        """Delete selected job"""
        current_row = self.jobs_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", 
                               "Please select a job to delete")
            return
        
        job_id = int(self.jobs_table.item(current_row, 0).text())
        job_number = self.jobs_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                    f"Delete job {job_number}?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Delete using repository directly
            success = self.job_service.repository.delete_job(job_id)
            if success:
                QMessageBox.information(self, "Success", "Job deleted")
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete job")
    
    def generate_report(self):
        """Generate report - let user choose format"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Report")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        label = QLabel("Select report format:")
        layout.addWidget(label)
        
        csv_radio = QRadioButton("CSV (Spreadsheet)")
        csv_radio.setChecked(True)
        layout.addWidget(csv_radio)
        
        json_radio = QRadioButton("JSON (Data)")
        layout.addWidget(json_radio)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            if csv_radio.isChecked():
                self.export_csv()
            else:
                self.export_json()
    
    def export_csv(self):
        """Export data to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "paint_jobs.csv", "CSV Files (*.csv)")
        
        if filename:
            if self.export_service.export_to_csv(filename):
                QMessageBox.information(self, "Success", 
                                       f"Data exported to {filename}")
            else:
                QMessageBox.critical(self, "Error", "Export failed")
    
    def export_json(self):
        """Export data to JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "paint_jobs.json", "JSON Files (*.json)")
        
        if filename:
            if self.export_service.export_to_json(filename):
                QMessageBox.information(self, "Success",
                                       f"Data exported to {filename}")
            else:
                QMessageBox.critical(self, "Error", "Export failed")
