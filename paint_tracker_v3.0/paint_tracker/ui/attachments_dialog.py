"""
Attachments Dialog
View, add, and manage file attachments for a job.

Author: Christopher Lajoie
"""

import os
import platform
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QFileDialog, QMessageBox, QHeaderView,
    QLineEdit, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
from paint_tracker.core.attachment_service import AttachmentService


class AttachmentsDialog(QDialog):
    """Dialog for managing job attachments"""
    
    def __init__(self, job_number: str, attachment_service: AttachmentService, 
                 current_user: str = "", parent=None):
        super().__init__(parent)
        self.job_number = job_number
        self.attachment_service = attachment_service
        self.current_user = current_user
        
        self.setWindowTitle(f"Attachments - Job #{job_number}")
        self.setMinimumSize(700, 400)
        self.setup_ui()
        self.load_attachments()
    
    def setup_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<h3>📎 Attachments for Job #{self.job_number}</h3>")
        layout.addWidget(header)
        
        # Attachments table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Filename", "Size", "Description", "Uploaded By", "Date"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Light gray selection
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #E8E8E8;
                color: black;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Attachment...")
        add_btn.clicked.connect(self.add_attachment)
        button_layout.addWidget(add_btn)
        
        open_btn = QPushButton("📄 Open")
        open_btn.clicked.connect(self.open_attachment)
        button_layout.addWidget(open_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_attachment)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def load_attachments(self):
        """Load attachments from database"""
        self.table.setRowCount(0)
        attachments = self.attachment_service.get_attachments(self.job_number)
        
        for attachment in attachments:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Store attachment ID in first column
            filename_item = QTableWidgetItem(attachment['original_filename'])
            filename_item.setData(Qt.UserRole, attachment['id'])
            filename_item.setData(Qt.UserRole + 1, attachment['file_path'])
            self.table.setItem(row, 0, filename_item)
            
            # Size in KB/MB
            size = attachment['file_size']
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            self.table.setItem(row, 1, QTableWidgetItem(size_str))
            
            # Description
            desc = attachment.get('description', '') or ''
            self.table.setItem(row, 2, QTableWidgetItem(desc))
            
            # Uploaded by
            uploaded_by = attachment.get('uploaded_by', '') or 'Unknown'
            self.table.setItem(row, 3, QTableWidgetItem(uploaded_by))
            
            # Date
            date_str = attachment.get('uploaded_at', '')
            if date_str:
                # Format: YYYY-MM-DD HH:MM:SS -> MM/DD/YYYY
                try:
                    if 'T' in date_str:
                        date_part = date_str.split('T')[0]
                    else:
                        date_part = date_str.split()[0]
                    parts = date_part.split('-')
                    date_str = f"{parts[1]}/{parts[2]}/{parts[0]}"
                except:
                    pass
            self.table.setItem(row, 4, QTableWidgetItem(date_str))
        
        # Update info label
        count = len(attachments)
        total_size = sum(att['file_size'] for att in attachments)
        if total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        
        self.info_label.setText(f"{count} attachment(s) • Total size: {size_str}")
    
    def add_attachment(self):
        """Add a new attachment"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF to Attach",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ask for description
        from PySide6.QtWidgets import QInputDialog
        description, ok = QInputDialog.getText(
            self,
            "Attachment Description",
            "Description (optional):",
            text=Path(file_path).stem
        )
        
        if not ok:
            return
        
        # Add attachment
        success, message = self.attachment_service.add_attachment(
            self.job_number,
            file_path,
            description,
            self.current_user
        )
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.load_attachments()
        else:
            QMessageBox.warning(self, "Error", message)
    
    def open_attachment(self):
        """Open selected attachment"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an attachment to open.")
            return
        
        file_path_item = self.table.item(current_row, 0)
        file_path = file_path_item.data(Qt.UserRole + 1)
        
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The attachment file could not be found:\n{file_path}"
            )
            return
        
        # Open file with system default application
        try:
            if platform.system() == 'Darwin':       # macOS
                subprocess.run(['open', file_path])
            elif platform.system() == 'Windows':    # Windows
                os.startfile(file_path)
            else:                                    # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to open file:\n{str(e)}"
            )
    
    def delete_attachment(self):
        """Delete selected attachment"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an attachment to delete.")
            return
        
        filename_item = self.table.item(current_row, 0)
        attachment_id = filename_item.data(Qt.UserRole)
        filename = filename_item.text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this attachment?\n\n{filename}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Delete attachment
        success, message = self.attachment_service.delete_attachment(attachment_id)
        
        if success:
            QMessageBox.information(self, "Success", "Attachment deleted successfully")
            self.load_attachments()
        else:
            QMessageBox.warning(self, "Error", message)
