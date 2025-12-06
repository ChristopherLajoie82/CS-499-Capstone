"""
Presentation Layer for Paint Tracking Program
Modern UI implementation using PySide6 Qt framework
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from PySide6.QtCore import Qt, Slot, QSettings, QEvent, QObject
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QRadioButton, QButtonGroup,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QGroupBox, QMessageBox, QFileDialog, QDialog, QDialogButtonBox,
    QFormLayout, QTabWidget, QSplitter, QStatusBar
)

from paint_tracker.core import (
    JobService, ExportService, BackupService,
    AuthenticationService
)
from paint_tracker.ui.dialogs import (
    JobFormDialog,
    LoginDialog,
    InitialSetupDialog,
    ChangePasswordDialog,
    CreateUserDialog
)


# ---------- Constants ----------

APP_VERSION = "3.0"


# ---------- Utilities ----------

def format_iso_date(iso_string: str) -> str:
    """Format ISO date string to MM/DD/YYYY HH:MM AM/PM"""
    if not iso_string:
        return ""
    try:
        if 'T' in iso_string:
            date_part, time_part = iso_string.split('T')
            time_part = time_part.split('+')[0].split('Z')[0]
            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except Exception:
        return iso_string


# ---------- Styling ----------

class StyleSheet:
    MAIN_STYLE = """
    QMainWindow { background-color: #f5f5f5; }
    QGroupBox {
        font-weight: bold;
        border: 2px solid #cccccc;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
    QPushButton {
        background-color: #4CAF50; color: white; border: none;
        padding: 8px 16px; border-radius: 4px; font-weight: bold; min-width: 100px;
    }
    QPushButton:hover { background-color: #45a049; }
    QPushButton:pressed { background-color: #3d8b40; }
    QPushButton:disabled { background-color: #cccccc; color: #666666; }
    QPushButton.danger { background-color: #f44336; }
    QPushButton.danger:hover { background-color: #da190b; }
    QPushButton.secondary { background-color: #008CBA; }
    QPushButton.secondary:hover { background-color: #007399; }

    QLineEdit, QDoubleSpinBox {
        padding: 8px; border: 1px solid #ddd; border-radius: 4px; background-color: white;
    }
    QLineEdit:focus, QDoubleSpinBox:focus { border-color: #4CAF50; outline: none; }

    QTableWidget { background-color: white; alternate-background-color: #f9f9f9; gridline-color: #ddd; }
    QHeaderView::section { 
        background-color: #4CAF50; 
        color: white; 
        padding: 8px; 
        border: 1px solid #2d7a2f;
        border-left: none;
        font-weight: bold; 
    }
    QHeaderView::section:first {
        border-left: 1px solid #2d7a2f;
    }

    QStatusBar { background-color: #333; color: white; }
    QMenuBar { background-color: white; border-bottom: 1px solid #ddd; }
    QMenuBar::item:selected { background-color: #4CAF50; color: white; }
    QMenu::item:selected { background-color: #4CAF50; color: white; }
    """


# ---------- Dialogs ----------

class MixDetailDialog(QDialog):
    """Dialog showing full details of a single mix entry, including notes"""

    def __init__(self, mix_data: Dict, parent=None):
        super().__init__(parent)
        self.mix_data = mix_data
        self.setWindowTitle("Mix Details")
        self.setModal(True)
        self.setMinimumSize(500, 450)

        layout = QVBoxLayout(self)

        # Header
        title = QLabel("Mix Entry Details")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        # Details section using form layout
        details_group = QGroupBox("Mix Information")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Format the date nicely
        date_str = str(mix_data.get("created_at", ""))
        date_formatted = format_iso_date(date_str)

        fields = [
            ("Date Mixed:", date_formatted),
            ("Paint Code:", mix_data.get("paint_code", "")),
            ("Color Name:", mix_data.get("color_name", "")),
            ("Version:", mix_data.get("paint_version", "1.0")),
            ("Manufacturer:", mix_data.get("manufacturer", "")),
            ("Amount:", f"{mix_data.get('mixed_amount', 0)}g"),
            ("Job Type:", (mix_data.get("job_type", "") or "").upper()),
            ("Mixed By:", mix_data.get("mixed_by", "")),
        ]

        for label_text, value in fields:
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold;")
            value_label = QLabel(str(value) if value else "-")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            form_layout.addRow(label, value_label)

        details_group.setLayout(form_layout)
        layout.addWidget(details_group)

        # Notes section with scrollable text area
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()

        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        self.notes_display.setMinimumHeight(120)
        notes_text = mix_data.get("notes", "")
        self.notes_display.setPlainText(notes_text if notes_text else "No notes for this entry")
        notes_layout.addWidget(self.notes_display)

        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class JobHistoryDialog(QDialog):
    """Dialog showing complete history of mixes for a job"""

    def __init__(self, job_service: JobService, job_number: str, attachment_service=None, current_user="", parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.job_number = job_number
        self.attachment_service = attachment_service
        self.current_user = current_user
        self.details: Dict = {}
        self.mix_entries: List[Dict] = []  # Store mix data for detail view
        self.setWindowTitle(f"Job History - {job_number}")
        self.setModal(True)
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # header
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)

        title = QLabel(f"Job Number: {self.job_number}")
        f = QFont()
        f.setPointSize(16)
        f.setBold(True)
        title.setFont(f)
        header_layout.addWidget(title)

        stats_row = QHBoxLayout()
        self.total_colors_label = QLabel("Total Colors: 0")
        self.total_amount_label = QLabel("Total Paint: 0 grams")
        self.date_range_label = QLabel("Date Range: -")
        stats_row.addWidget(self.total_colors_label)
        stats_row.addWidget(self.total_amount_label)
        stats_row.addWidget(self.date_range_label)
        stats_row.addStretch()
        header_layout.addLayout(stats_row)

        layout.addWidget(header_frame)

        # hint label for double-click
        hint_label = QLabel("Double-click a row to view full details including notes")
        hint_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(hint_label)

        # table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #d0d0d0;
                color: black;
            }
        """)
        
        # Connect double-click to show details
        self.table.cellDoubleClicked.connect(self.show_mix_details)
        
        # Enable click on empty space to deselect
        self.table.viewport().installEventFilter(self)

        cols = [
            "Date Mixed", "Paint Code", "Color Name", "Version",
            "Manufacturer", "Amount", "Job Type", "Mixed By", "Notes"
        ]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        layout.addWidget(self.table)

        # buttons
        row_btns = QHBoxLayout()
        
        # Attachments button (if attachment service available)
        if self.attachment_service:
            attachments_btn = QPushButton("📎 Attachments")
            attachments_btn.clicked.connect(self.open_attachments)
            row_btns.addWidget(attachments_btn)
        
        export_btn = QPushButton("Export History")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_history)
        row_btns.addWidget(export_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load)
        row_btns.addWidget(refresh_btn)

        row_btns.addStretch()
        
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(self.delete_selected_entry)
        row_btns.addWidget(delete_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        row_btns.addWidget(close_btn)

        layout.addLayout(row_btns)

        self.load()

    @Slot()
    def load(self):
        self.details = self.job_service.repository.get_job_details(self.job_number)
        self.mix_entries = self.details.get("history", [])  # Store for detail view

        self.total_colors_label.setText(f"Total Colors: {self.details['total_colors']}")
        self.total_amount_label.setText(f"Total Paint: {self.details['total_amount']:.2f} grams")

        first = format_iso_date(self.details["date_range"]["first"])
        last = format_iso_date(self.details["date_range"]["last"])
        self.date_range_label.setText(
            f"Date Range: {first} to {last}" if first and last else "Date Range: No mixes yet"
        )

        self.table.setRowCount(0)
        for e in self.details["history"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(format_iso_date(str(e.get("created_at", "")))))
            self.table.setItem(row, 1, QTableWidgetItem(e.get("paint_code", "")))
            self.table.setItem(row, 2, QTableWidgetItem(e.get("color_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(e.get("paint_version", "1.0")))
            self.table.setItem(row, 4, QTableWidgetItem(e.get("manufacturer", "")))
            self.table.setItem(row, 5, QTableWidgetItem(f"{e.get('mixed_amount', 0)}g"))
            job_type = e.get("job_type", "")
            self.table.setItem(row, 6, QTableWidgetItem(job_type.upper() if job_type else ""))
            self.table.setItem(row, 7, QTableWidgetItem(e.get("mixed_by", "")))
            self.table.setItem(row, 8, QTableWidgetItem(e.get("notes", "")))

    @Slot(int, int)
    def show_mix_details(self, row: int, column: int):
        """Show detail dialog for the selected mix entry"""
        if 0 <= row < len(self.mix_entries):
            mix_data = self.mix_entries[row]
            dialog = MixDetailDialog(mix_data, self)
            dialog.exec()

    @Slot()
    def delete_selected_entry(self):
        """Delete the selected mix entry"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an entry to delete")
            return
        
        if current_row >= len(self.mix_entries):
            return
        
        entry = self.mix_entries[current_row]
        entry_id = entry.get("id")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete this mix entry?\n\nPaint Code: {entry.get('paint_code', '')}\nColor: {entry.get('color_name', '')}\nAmount: {entry.get('mixed_amount', 0)}g",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.job_service.repository.delete_job(entry_id)
            if success:
                QMessageBox.information(self, "Deleted", "Entry deleted successfully")
                self.load()  # Refresh the table
            else:
                QMessageBox.critical(self, "Error", "Failed to delete entry")

    @Slot()
    def open_attachments(self):
        """Open attachments dialog for this job"""
        if not self.attachment_service:
            return
        
        from paint_tracker.ui.attachments_dialog import AttachmentsDialog
        dialog = AttachmentsDialog(
            self.job_number,
            self.attachment_service,
            self.current_user,
            self
        )
        dialog.exec()
    
    @Slot()
    def export_history(self):
        """Export job history to CSV or JSON file"""
        # Ask user for format preference
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Format")
        msg.setText(f"Export history for Job {self.job_number}")
        msg.setInformativeText("Choose export format:")
        
        csv_btn = msg.addButton("CSV (Excel)", QMessageBox.ActionRole)
        json_btn = msg.addButton("JSON (Data)", QMessageBox.ActionRole)
        cancel_btn = msg.addButton(QMessageBox.Cancel)
        
        msg.exec()
        clicked = msg.clickedButton()
        
        if clicked == cancel_btn:
            return
        elif clicked == csv_btn:
            self.export_to_csv()
        elif clicked == json_btn:
            self.export_to_json()
    
    def export_to_csv(self):
        """Export history to CSV file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Export History for Job {self.job_number}",
            f"job_{self.job_number}_history.csv", "CSV Files (*.csv)"
        )
        if not filename:
            return
        try:
            import csv
            with open(filename, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([
                    "Job Number", "Date Mixed", "Color Name", "Paint Code",
                    "Version", "Manufacturer", "Amount", "Mixed By", "Notes"
                ])
                for e in self.details["history"]:
                    w.writerow([
                        e.get("job_number", self.job_number),
                        e.get("created_at", ""),
                        e.get("color_name", ""),
                        e.get("paint_code", ""),
                        e.get("paint_version", "1.0"),
                        e.get("manufacturer", ""),
                        e.get("mixed_amount", 0),
                        e.get("mixed_by", ""),
                        e.get("notes", "")
                    ])
            QMessageBox.information(self, "Success", f"History exported to {filename}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to export: {ex}")
    
    def export_to_json(self):
        """Export history to JSON file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Export History for Job {self.job_number}",
            f"job_{self.job_number}_history.json", "JSON Files (*.json)"
        )
        if not filename:
            return
        try:
            import json
            export_data = {
                "job_number": self.job_number,
                "total_colors": self.details.get("total_colors", 0),
                "total_amount": self.details.get("total_amount", 0),
                "date_range": self.details.get("date_range", {}),
                "history": self.details.get("history", [])
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)
            QMessageBox.information(self, "Success", f"History exported to {filename}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to export: {ex}")
    
    def eventFilter(self, obj, event):
        """Handle click on empty space to deselect"""
        if obj == self.table.viewport() and event.type() == QEvent.MouseButtonPress:
            # Get the item at the clicked position
            item = self.table.itemAt(event.pos())
            if item is None:
                # Clicked on empty space - clear selection
                self.table.clearSelection()
        return False  # Let the event continue to be processed


# ---------- Dashboard ----------

class DashboardWidget(QWidget):
    """Main dashboard with summary list and actions"""

    def __init__(self, job_service: JobService, export_service: ExportService, 
                 auth_service=None, attachment_service=None, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.export_service = export_service
        self.auth_service = auth_service
        self.attachment_service = attachment_service
        self.job_summaries: List[Dict] = []
        self.search_query = ""
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # top splitter
        top = QSplitter(Qt.Horizontal)

        # search panel - compact
        search_group = QGroupBox("Search Filter")
        search_group.setMaximumHeight(120)  # Make search panel shorter
        s_layout = QVBoxLayout(search_group)
        s_layout.setSpacing(5)  # Reduce spacing for compact look

        row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by job number, paint code, or color")
        self.search_edit.textChanged.connect(self.on_search_changed)
        row.addWidget(self.search_edit)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.perform_search)
        row.addWidget(btn_search)

        btn_clear = QPushButton("Clear")
        btn_clear.setProperty("class", "secondary")
        btn_clear.clicked.connect(self.clear_search)
        row.addWidget(btn_clear)

        s_layout.addLayout(row)

        self.filter_group = None  # Keep for compatibility but set to None

        top.addWidget(search_group)

        # stats panel - scrollable to match search panel height
        stats_group = QGroupBox("Statistics")
        stats_group.setMaximumHeight(120)  # Same height as search panel
        
        # Create scroll area for stats
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #f0f0f0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
        """)
        
        # Widget to hold the stats content
        stats_content = QWidget()
        f = QFormLayout(stats_content)
        f.setContentsMargins(0, 0, 10, 0)  # Add right margin for scrollbar
        self.stats_labels = {
            "total_jobs": QLabel("0"),
            "recent_jobs": QLabel("0"),
            "total_paint": QLabel("0 grams"),
            "avg": QLabel("0 grams"),
            "most_used_code": QLabel("-"),
            "most_active_operator": QLabel("-"),
            "avg_mix_size": QLabel("0 grams"),
            "top_manufacturer": QLabel("-")
        }
        for label in self.stats_labels.values():
            label.setAlignment(Qt.AlignRight)

        f.addRow("Total Jobs:", self.stats_labels["total_jobs"])
        f.addRow("Recent 30 days:", self.stats_labels["recent_jobs"])
        f.addRow("Total Paint Mixed:", self.stats_labels["total_paint"])
        f.addRow("Average per Job:", self.stats_labels["avg"])
        
        # Add separator for new stats
        separator = QLabel("──────────────")
        separator.setAlignment(Qt.AlignCenter)
        f.addRow("", separator)
        
        f.addRow("Top Paint Code:", self.stats_labels["most_used_code"])
        f.addRow("Most Active Operator:", self.stats_labels["most_active_operator"])
        f.addRow("Avg Mix Size:", self.stats_labels["avg_mix_size"])
        f.addRow("Top Manufacturer:", self.stats_labels["top_manufacturer"])
        
        scroll.setWidget(stats_content)
        
        # Layout for stats group
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(5, 5, 5, 5)
        stats_layout.addWidget(scroll)

        top.addWidget(stats_group)
        top.setStretchFactor(0, 2)
        top.setStretchFactor(1, 1)
        layout.addWidget(top)

        # action buttons
        actions = QHBoxLayout()
        btn_new = QPushButton("New Job")
        btn_new.clicked.connect(self.create_new_job)
        actions.addWidget(btn_new)

        btn_view = QPushButton("View Job History")
        btn_view.setProperty("class", "secondary")
        btn_view.clicked.connect(self.view_job_history)
        actions.addWidget(btn_view)

        btn_del = QPushButton("Delete Job")
        btn_del.setProperty("class", "danger")
        btn_del.clicked.connect(self.delete_selected_job)
        actions.addWidget(btn_del)

        actions.addStretch()

        btn_report = QPushButton("Generate Report")
        btn_report.clicked.connect(self.generate_report)
        actions.addWidget(btn_report)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_data)
        actions.addWidget(btn_refresh)

        layout.addLayout(actions)

        # table
        self.jobs_table = QTableWidget()
        self.jobs_table.setAlternatingRowColors(True)
        self.jobs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.jobs_table.setSelectionMode(QTableWidget.SingleSelection)
        self.jobs_table.setSortingEnabled(True)
        
        # Make grid lines visible
        self.jobs_table.setShowGrid(True)
        self.jobs_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #cccccc;
                border: 1px solid #cccccc;
            }
            QTableWidget::item:selected {
                background-color: #d0d0d0;
                color: black;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-right: 2px solid #2d7a2f;
                border-bottom: 2px solid #2d7a2f;
            }
            QHeaderView::section:last {
                border-right: none;
            }
        """)

        headers = ["Job Number", "Last Mixed", "Paint Code", "Color Name", "Total Amount Mixed", "Number of Mixes", "Mixed By"]
        self.jobs_table.setColumnCount(len(headers))
        self.jobs_table.setHorizontalHeaderLabels(headers)
        h = self.jobs_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        
        self.jobs_table.setColumnWidth(0, 100)  # Job Number
        self.jobs_table.setColumnWidth(1, 150)  # Last Mixed
        self.jobs_table.setColumnWidth(2, 100)  # Paint Code
        self.jobs_table.setColumnWidth(3, 120)  # Color Name
        self.jobs_table.setColumnWidth(4, 130)  # Total Amount Mixed
        self.jobs_table.setColumnWidth(5, 100)  # Number of Mixes
        
        h.setStretchLastSection(True)  # Mixed By stretches to fill

        # double click opens history
        self.jobs_table.itemDoubleClicked.connect(self.view_job_history)
        
        # Enable click on empty space to deselect
        self.jobs_table.viewport().installEventFilter(self)

        layout.addWidget(self.jobs_table)

    # ---- helpers ----

    def add_summary_to_table(self, summary: dict):
        row = self.jobs_table.rowCount()
        self.jobs_table.insertRow(row)

        job_no = str(summary.get("job_number", ""))
        
        # Check if job has attachments
        attachment_count = 0
        if self.attachment_service:
            attachment_count = self.attachment_service.get_attachment_count(job_no)
        
        # Add paperclip icon if attachments exist
        job_display = f"📎 {job_no}" if attachment_count > 0 else job_no

        col0 = QTableWidgetItem(job_display)
        col0.setData(Qt.UserRole, job_no)  # store for double click
        self.jobs_table.setItem(row, 0, col0)

        entry_count = summary.get("entry_count", 0)
        total_amount = summary.get("total_amount", 0)

        last_mixed = summary.get("last_mixed", "")
        last_mixed_formatted = format_iso_date(last_mixed) or "N/A"

        mixed_by = summary.get("mixed_by", "Unknown")
        paint_code = summary.get("paint_code", "")
        color_name = summary.get("color_name", "")

        self.jobs_table.setItem(row, 1, QTableWidgetItem(last_mixed_formatted))
        self.jobs_table.setItem(row, 2, QTableWidgetItem(paint_code))
        self.jobs_table.setItem(row, 3, QTableWidgetItem(color_name))
        self.jobs_table.setItem(row, 4, QTableWidgetItem(f"{total_amount}g"))
        self.jobs_table.setItem(row, 5, QTableWidgetItem(str(entry_count)))
        self.jobs_table.setItem(row, 6, QTableWidgetItem(mixed_by))

    def rebuild_summary_rows(self, items: List[dict]):
        self.jobs_table.setRowCount(0)
        for s in items:
            self.add_summary_to_table(s)

    # ---- slots ----

    @Slot()
    def refresh_data(self):
        self.job_summaries = self.job_service.repository.get_job_summaries()
        self.rebuild_summary_rows(self.job_summaries)
        self.update_statistics()

    @Slot(str)
    def on_search_changed(self, text: str):
        self.search_query = (text or "").strip().lower()
        self.perform_search()

    @Slot()
    def perform_search(self):
        q = self.search_query or self.search_edit.text().strip().lower()

        if not q:
            self.rebuild_summary_rows(self.job_summaries)
            return

        filtered = []
        for s in self.job_summaries:
            job_no = str(s.get("job_number", ""))
            mixed_by = str(s.get("mixed_by", ""))
            paint_code = str(s.get("paint_code", ""))
            color_name = str(s.get("color_name", ""))
            hay = f"{job_no} {mixed_by} {paint_code} {color_name}".lower()
            if q in hay:
                filtered.append(s)

        self.rebuild_summary_rows(filtered)

    @Slot()
    def clear_search(self):
        self.search_edit.clear()
        self.rebuild_summary_rows(self.job_summaries)

    @Slot()
    def view_job_history(self):
        row = self.jobs_table.currentRow()
        if row < 0:
            return
        item0 = self.jobs_table.item(row, 0)
        if not item0:
            return
        job_number = item0.data(Qt.UserRole) or item0.text()
        if not job_number:
            return

        # Get current username for attachments
        current_user = ""
        if self.auth_service:
            user = self.auth_service.get_current_user()
            if user:
                current_user = user.get('username', '')
        
        dlg = JobHistoryDialog(
            self.job_service, 
            job_number,
            self.attachment_service,
            current_user,
            parent=self
        )
        dlg.exec()
        self.refresh_data()

    @Slot()
    def create_new_job(self):
        # Get current username for auto-populating Mixed By field
        current_username = None
        if self.auth_service:
            user = self.auth_service.get_current_user()
            if user:
                current_username = user.get('username')
        
        dlg = JobFormDialog(self.job_service, job_data=None, current_username=current_username, parent=self)
        if dlg.exec():
            self.refresh_data()

    @Slot()
    def delete_selected_job(self):
        row = self.jobs_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a job to delete")
            return
        item0 = self.jobs_table.item(row, 0)
        if not item0:
            return
        job_number = item0.data(Qt.UserRole) or item0.text()
        if not job_number:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete ALL paint mixes for job {job_number}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        ok = self.job_service.repository.delete_job_by_number(job_number)
        if ok:
            QMessageBox.information(self, "Deleted", f"All entries for job {job_number} deleted")
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to delete job")

    @Slot()
    def generate_report(self):
        """Generate report - let user choose format"""
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
        filename, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv)")
        if not filename:
            return
        if self.export_service.export_to_csv(filename):
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        else:
            QMessageBox.critical(self, "Error", "Failed to export data")

    @Slot()
    def export_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export to JSON", "", "JSON Files (*.json)")
        if not filename:
            return
        if self.export_service.export_to_json(filename):
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        else:
            QMessageBox.critical(self, "Error", "Failed to export data")

    def update_statistics(self):
        stats = self.job_service.get_statistics()
        self.stats_labels["total_jobs"].setText(str(stats.get("total_jobs", 0)))
        self.stats_labels["recent_jobs"].setText(str(stats.get("recent_jobs", 0)))
        self.stats_labels["total_paint"].setText(f"{stats.get('total_paint', 0)} grams")
        avg = stats.get("average_paint_per_job", 0)
        self.stats_labels["avg"].setText(f"{avg} grams")
        
        # Calculate additional statistics
        try:
            from datetime import datetime, timedelta
            from collections import Counter
            
            # Get all jobs from last 30 days for monthly stats
            all_jobs = self.job_service.repository.get_all_jobs()
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_jobs = []
            
            for job in all_jobs:
                try:
                    job_date = job.get('created_at', '')
                    if job_date:
                        if 'T' in job_date:
                            date_part = job_date.split('T')[0]
                            job_datetime = datetime.strptime(date_part, "%Y-%m-%d")
                        else:
                            job_datetime = datetime.strptime(job_date[:10], "%Y-%m-%d")
                        
                        if job_datetime >= cutoff_date:
                            recent_jobs.append(job)
                except:
                    continue
            
            # Most used paint code this month
            if recent_jobs:
                paint_codes = [j.get('paint_code', '') for j in recent_jobs if j.get('paint_code')]
                if paint_codes:
                    most_common_code = Counter(paint_codes).most_common(1)[0]
                    self.stats_labels["most_used_code"].setText(f"{most_common_code[0]} ({most_common_code[1]}x)")
                else:
                    self.stats_labels["most_used_code"].setText("-")
                
                # Most active operator
                operators = [j.get('mixed_by', '') for j in recent_jobs if j.get('mixed_by')]
                if operators:
                    most_active_op = Counter(operators).most_common(1)[0]
                    self.stats_labels["most_active_operator"].setText(f"{most_active_op[0]} ({most_active_op[1]})")
                else:
                    self.stats_labels["most_active_operator"].setText("-")
                
                # Average mix size (recent)
                amounts = [float(j.get('mixed_amount', 0)) for j in recent_jobs if j.get('mixed_amount')]
                if amounts:
                    avg_mix = sum(amounts) / len(amounts)
                    self.stats_labels["avg_mix_size"].setText(f"{avg_mix:.1f}g")
                else:
                    self.stats_labels["avg_mix_size"].setText("0g")
            else:
                self.stats_labels["most_used_code"].setText("-")
                self.stats_labels["most_active_operator"].setText("-")
                self.stats_labels["avg_mix_size"].setText("0g")
            
            # Top manufacturer (all time)
            if all_jobs:
                manufacturers = [j.get('manufacturer', '') for j in all_jobs if j.get('manufacturer')]
                if manufacturers:
                    top_mfg = Counter(manufacturers).most_common(1)[0]
                    self.stats_labels["top_manufacturer"].setText(f"{top_mfg[0]} ({top_mfg[1]})")
                else:
                    self.stats_labels["top_manufacturer"].setText("-")
            else:
                self.stats_labels["top_manufacturer"].setText("-")
                
        except Exception as e:
            # If there's an error calculating enhanced stats, just leave defaults
            pass

    def eventFilter(self, obj, event):
        if obj == self.jobs_table.viewport():
            if event.type() == QEvent.MouseButtonPress:
                index = self.jobs_table.indexAt(event.pos())
                if not index.isValid():
                    self.jobs_table.clearSelection()
        return super().eventFilter(obj, event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts in the dashboard"""
        from PySide6.QtCore import Qt
        
        # Ctrl+F to focus search box
        if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
            return
        
        # Check if table has focus for table-specific shortcuts
        if self.jobs_table.hasFocus():
            # Delete key to delete selected job
            if event.key() == Qt.Key_Delete:
                row = self.jobs_table.currentRow()
                if row >= 0:
                    # Add confirmation dialog
                    reply = QMessageBox.question(self, "Confirm Delete", 
                                                "Delete selected job entry?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.delete_selected_job()
                return
            
            # Enter/Return to open job history
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                row = self.jobs_table.currentRow()
                if row >= 0:
                    self.view_job_history()
                return
        
        super().keyPressEvent(event)


# ---------- Admin ----------

class AdminDialog(QDialog):
    def __init__(self, backup_service: BackupService, auth_service: AuthenticationService, parent=None):
        super().__init__(parent)
        self.backup_service = backup_service
        self.auth_service = auth_service
        self.setWindowTitle("Administrator Mode")
        self.setModal(True)
        self.setMinimumSize(600, 420)

        # Build admin panel directly since user already authenticated
        self._build_admin()

    def _build_admin(self):
        v = QVBoxLayout(self)

        t = QLabel("Administrator Options")
        t.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        t.setFont(f)
        v.addWidget(t)

        tabs = QTabWidget()

        # backup tab
        tab_b = QWidget()
        vb = QVBoxLayout(tab_b)
        btn_create = QPushButton("Create Backup")
        btn_create.clicked.connect(self.create_backup)
        vb.addWidget(btn_create)

        btn_manage = QPushButton("Manage Backups")
        btn_manage.clicked.connect(self.manage_backups)
        vb.addWidget(btn_manage)
        vb.addStretch()
        tabs.addTab(tab_b, "Backup Management")

        # User Management tab (new)
        tab_u = QWidget()
        vu = QVBoxLayout(tab_u)
        btn_create_user = QPushButton("Create New User")
        btn_create_user.clicked.connect(self.create_new_user)
        vu.addWidget(btn_create_user)
        
        btn_view_users = QPushButton("View All Users")
        btn_view_users.clicked.connect(self.view_users)
        vu.addWidget(btn_view_users)
        vu.addStretch()
        tabs.addTab(tab_u, "User Management")

        # security tab
        tab_s = QWidget()
        vs = QVBoxLayout(tab_s)
        
        # Show bcrypt status
        status_label = QLabel(self.auth_service.bcrypt_status())
        status_label.setStyleSheet("color: #666; font-style: italic;")
        vs.addWidget(status_label)
        vs.addSpacing(10)
        
        btn_change = QPushButton("Change My Password")
        btn_change.clicked.connect(self.change_my_password)
        vs.addWidget(btn_change)
        vs.addStretch()
        tabs.addTab(tab_s, "Security")

        v.addWidget(tabs)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        v.addWidget(btn_close)

    @Slot()
    def create_backup(self):
        if self.backup_service.create_backup():
            QMessageBox.information(self, "Success", "Backup created")
        else:
            QMessageBox.critical(self, "Error", "Failed to create backup")

    @Slot()
    def manage_backups(self):
        backups = self.backup_service.list_backups()
        if not backups:
            QMessageBox.information(self, "No Backups", "No backups found. Click 'Create Backup' to create one.")
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Manage Backups")
        dlg.setMinimumSize(650, 400)
        v = QVBoxLayout(dlg)
        
        # Instructions
        info = QLabel("Select a backup and click 'Restore' to restore your database to that point.")
        info.setStyleSheet("color: #666; font-style: italic;")
        v.addWidget(info)
        
        # Table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Filename", "Size", "Created", "Action"])
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 200)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 100)
        table.setRowCount(len(backups))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        for i, b in enumerate(backups):
            size_kb = b["size"] / 1024
            table.setItem(i, 0, QTableWidgetItem(b["filename"]))
            table.setItem(i, 1, QTableWidgetItem(f"{size_kb:.1f} KB"))
            table.setItem(i, 2, QTableWidgetItem(b["created"]))
            
            # Restore button for each row
            restore_btn = QPushButton("Restore")
            restore_btn.setProperty("filename", b["filename"])
            restore_btn.clicked.connect(lambda checked, fn=b["filename"]: self._restore_selected(fn, dlg))
            table.setCellWidget(i, 3, restore_btn)
        
        v.addWidget(table)
        
        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        v.addWidget(btn_close)
        
        dlg.exec()
    
    def _restore_selected(self, filename: str, parent_dlg):
        """Restore a specific backup file"""
        reply = QMessageBox.question(
            parent_dlg, "Confirm Restore",
            f"Restore database from:\n{filename}\n\nThis will replace your current data. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.backup_service.restore_backup(filename):
                QMessageBox.information(parent_dlg, "Success", "Database restored successfully.\n\nPlease restart the application.")
                parent_dlg.accept()
            else:
                QMessageBox.critical(parent_dlg, "Error", "Failed to restore backup.")

    @Slot()
    def create_new_user(self):
        dlg = CreateUserDialog(self.auth_service, self)
        dlg.exec()

    @Slot()
    def view_users(self):
        users = self.auth_service.get_all_users()
        if not users:
            QMessageBox.information(self, "No Users", "No users found")
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle("User Management")
        dlg.setMinimumSize(700, 450)
        v = QVBoxLayout(dlg)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Username", "Role", "Status", "Created", "Last Login"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #d0d0d0;
                color: black;
            }
        """)
        
        def table_event_filter(obj, event):
            if obj == table.viewport():
                if event.type() == QEvent.MouseButtonPress:
                    index = table.indexAt(event.pos())
                    if not index.isValid():
                        table.clearSelection()
            return False
        
        class TableEventFilter(QObject):
            def __init__(self, parent=None):
                super().__init__(parent)
            
            def eventFilter(self, obj, event):
                return table_event_filter(obj, event)
        
        filter_obj = TableEventFilter()
        table.viewport().installEventFilter(filter_obj)
        
        def populate_table():
            current_users = self.auth_service.get_all_users()
            table.setRowCount(len(current_users))
            for i, u in enumerate(current_users):
                username_item = QTableWidgetItem(u["username"])
                username_item.setData(Qt.UserRole, u["id"])
                table.setItem(i, 0, username_item)
                table.setItem(i, 1, QTableWidgetItem(u["role"].upper()))
                status = "Active" if u["is_active"] else "Disabled"
                table.setItem(i, 2, QTableWidgetItem(status))
                table.setItem(i, 3, QTableWidgetItem(u["created_at"] or ""))
                table.setItem(i, 4, QTableWidgetItem(u["last_login"] or "Never"))
        
        populate_table()
        v.addWidget(table)
        
        btn_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Delete User")
        delete_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px 16px;")
        
        def delete_selected_user():
            row = table.currentRow()
            if row < 0:
                QMessageBox.warning(dlg, "No Selection", "Please select a user to delete")
                return
            
            username_item = table.item(row, 0)
            user_id = username_item.data(Qt.UserRole)
            username = username_item.text()
            
            current_user = self.auth_service.get_current_user()
            if current_user and current_user['id'] == user_id:
                QMessageBox.warning(dlg, "Cannot Delete", "You cannot delete your own account")
                return
            
            reply = QMessageBox.question(
                dlg, "Confirm Delete",
                f"Are you sure you want to delete user '{username}'?\n\n"
                "Note: Job records created by this user will be preserved.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success, message = self.auth_service.delete_user(user_id)
                if success:
                    QMessageBox.information(dlg, "Success", f"User '{username}' deleted successfully")
                    populate_table()
                else:
                    QMessageBox.critical(dlg, "Error", message)
        
        delete_btn.clicked.connect(delete_selected_user)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 16px;")
        close_btn.clicked.connect(dlg.accept)
        btn_layout.addWidget(close_btn)
        
        v.addLayout(btn_layout)
        dlg.exec()

    @Slot()
    def change_my_password(self):
        user = self.auth_service.get_current_user()
        if user:
            dlg = ChangePasswordDialog(self.auth_service, user['id'], self)
            dlg.exec()


# ---------- Main Window and App ----------

class MainWindow(QMainWindow):
    def __init__(self, job_service: JobService, export_service: ExportService, 
                 backup_service: BackupService, auth_service: AuthenticationService,
                 attachment_service):
        super().__init__()
        self.job_service = job_service
        self.export_service = export_service
        self.backup_service = backup_service
        self.auth_service = auth_service
        self.attachment_service = attachment_service

        self.setWindowTitle("Paint Tracking System v2.0")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)

        self._build_ui()
        self._menus()
        self._toolbar()
        self._status()

    def _build_ui(self):
        tabs = QTabWidget()
        self.dashboard = DashboardWidget(
            self.job_service, 
            self.export_service, 
            self.auth_service,
            self.attachment_service
        )
        tabs.addTab(self.dashboard, "Dashboard")
        self.setCentralWidget(tabs)

    def _menus(self):
        mb = self.menuBar()

        m_file = mb.addMenu("&File")
        act_new = QAction("&New Job", self); act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self.dashboard.create_new_job)
        m_file.addAction(act_new)

        m_file.addSeparator()
        act_csv = QAction("Export to &CSV", self)
        act_csv.setShortcut("Ctrl+E")  # Add shortcut
        act_csv.triggered.connect(self.dashboard.export_csv)
        m_file.addAction(act_csv)
        act_json = QAction("Export to &JSON", self)
        act_json.triggered.connect(self.dashboard.export_json)
        m_file.addAction(act_json)

        m_file.addSeparator()
        act_exit = QAction("E&xit", self); act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        m_file.addAction(act_exit)

        m_edit = mb.addMenu("&Edit")
        act_refresh = QAction("&Refresh", self); act_refresh.setShortcut("F5")
        act_refresh.triggered.connect(self.dashboard.refresh_data)
        m_edit.addAction(act_refresh)

        m_tools = mb.addMenu("&Tools")
        act_admin = QAction("&Administrator Mode", self)
        act_admin.triggered.connect(self.open_admin)
        m_tools.addAction(act_admin)
        
        m_tools.addSeparator()
        act_change_pwd = QAction("Change &Password", self)
        act_change_pwd.triggered.connect(self.change_password)
        m_tools.addAction(act_change_pwd)
        
        # Admin-only menu items
        if self.auth_service.is_admin():
            m_tools.addSeparator()
            act_create_user = QAction("Create &User", self)
            act_create_user.triggered.connect(self.create_user)
            m_tools.addAction(act_create_user)
            
            # Database settings (admin only)
            m_tools.addSeparator()
            act_db_settings = QAction("&Database Settings", self)
            act_db_settings.triggered.connect(self.open_database_settings)
            m_tools.addAction(act_db_settings)
        
        m_tools.addSeparator()
        act_logout = QAction("&Logout", self)
        act_logout.triggered.connect(self.logout)
        m_tools.addAction(act_logout)

        m_help = mb.addMenu("&Help")
        act_about = QAction("&About", self)
        act_about.triggered.connect(self.show_about)
        m_help.addAction(act_about)

    def _toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(False)
        act_new = QAction("New Job", self)
        act_new.triggered.connect(self.dashboard.create_new_job)
        tb.addAction(act_new)
        tb.addSeparator()
        act_refresh = QAction("Refresh", self)
        act_refresh.triggered.connect(self.dashboard.refresh_data)
        tb.addAction(act_refresh)
        tb.addSeparator()
        act_admin = QAction("Admin", self)
        act_admin.triggered.connect(self.open_admin)
        tb.addAction(act_admin)

    def _status(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        
        # Show current user info
        user = self.auth_service.get_current_user()
        if user:
            role_text = " (Admin)" if user['role'] == 'admin' else ""
            sb.showMessage(f"Logged in as: {user['username']}{role_text}")
        else:
            sb.showMessage("Ready")

    @Slot()
    def open_admin(self):
        # Check if user has admin privileges
        if not self.auth_service.is_admin():
            QMessageBox.warning(
                self, "Access Denied",
                "Administrator privileges required."
            )
            return
        dlg = AdminDialog(self.backup_service, self.auth_service, self)
        dlg.exec()

    @Slot()
    def show_about(self):
        QMessageBox.about(
            self, "About Paint Tracking System",
            f"<h2>Paint Tracking System v{APP_VERSION}</h2>"
            "<p>Three-layer architecture with Python/Qt</p>"
            "<p>Created for CS 499 Computer Science Capstone</p>"
            "<p>Author: Christopher Lajoie</p>"
            "<ul>"
            "<li>PySide6 Qt</li>"
            "<li>SQLite</li>"
            "<li>Repository and Services</li>"
            "<li>bcrypt Authentication</li>"
            "</ul>"
        )

    @Slot()
    def change_password(self):
        user = self.auth_service.get_current_user()
        if user:
            dlg = ChangePasswordDialog(self.auth_service, user['id'], self)
            dlg.exec()

    @Slot()
    def create_user(self):
        if not self.auth_service.is_admin():
            QMessageBox.warning(
                self, "Access Denied",
                "Administrator privileges required to create users."
            )
            return
        dlg = CreateUserDialog(self.auth_service, self)
        dlg.exec()
    
    def open_database_settings(self):
        """Open database settings dialog (admin only)"""
        if not self.auth_service.is_admin():
            QMessageBox.warning(
                self, "Access Denied",
                "Administrator privileges required to change database settings."
            )
            return
        from paint_tracker.ui.database_settings_dialog import DatabaseSettingsDialog
        dlg = DatabaseSettingsDialog(self)
        dlg.exec()

    @Slot()
    def logout(self):
        reply = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.auth_service.logout()
            self._logout_requested = True
            self.close()
    
    def was_logout_requested(self):
        return getattr(self, '_logout_requested', False)


class PaintTrackerApplication:
    """Main application controller"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Paint Tracking System")
        self.app.setOrganizationName("SNHU CS499")

        self.app_dir = Path.home() / ".paint_tracker"
        self.app_dir.mkdir(exist_ok=True)

        self.config_file = self.app_dir / "config.json"
        self.database_path: Optional[str] = None
        self.settings = QSettings("SNHU", "PaintTracker")

        self._load_config()

    def _load_config(self):
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.database_path = cfg.get("database_path")
            except Exception:
                pass

    def _save_config(self):
        import json
        cfg = {"database_path": str(self.database_path), "version": APP_VERSION, "ui_framework": "PySide6"}
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _first_run_wizard(self) -> bool:
        dlg = QDialog()
        dlg.setWindowTitle("Paint Tracking System - Setup")
        dlg.setMinimumWidth(450)
        v = QVBoxLayout(dlg)

        t = QLabel("Welcome to Paint Tracking System")
        f = QFont(); f.setPointSize(16); f.setBold(True)
        t.setFont(f); t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        v.addWidget(QLabel("\nChoose how to set up your database:\n"))

        # Option 1: Create New Database
        btn_create = QPushButton("Create New Database")
        btn_create.setMinimumHeight(40)
        
        def create_new():
            name, _ = QFileDialog.getSaveFileName(
                dlg, "Create New Database",
                str(Path.home() / "paint_tracker.db"),
                "Database Files (*.db)"
            )
            if name:
                self.database_path = name
                self._save_config()
                dlg.accept()

        btn_create.clicked.connect(create_new)
        v.addWidget(btn_create)

        # Option 2: Load Existing Database
        btn_load = QPushButton("Load Existing Database")
        btn_load.setMinimumHeight(40)

        def load_existing():
            name, _ = QFileDialog.getOpenFileName(
                dlg, "Load Existing Database",
                str(Path.home()),
                "Database Files (*.db)"
            )
            if name:
                self.database_path = name
                self._save_config()
                dlg.accept()

        btn_load.clicked.connect(load_existing)
        v.addWidget(btn_load)

        v.addSpacing(10)

        # Cancel button
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dlg.reject)
        v.addWidget(btn_cancel)

        return dlg.exec() == QDialog.Accepted

    def initialize_services(self):
        self.job_service = JobService()
        self.export_service = ExportService()
        self.backup_service = BackupService(self.database_path, self.app_dir / "backups")
        self.auth_service = AuthenticationService()
        
        # Initialize attachment service
        from paint_tracker.core.attachment_service import AttachmentService
        attachments_dir = self.app_dir / "attachments"
        self.attachment_service = AttachmentService(attachments_dir)
        
        self.backup_service.create_backup()

    def run(self) -> int:
        if not self.database_path or not os.path.exists(self.database_path):
            if not self._first_run_wizard():
                return 1

        self.initialize_services()

        # Check if initial setup is needed (no users exist)
        if self.auth_service.needs_initial_setup():
            setup_dlg = InitialSetupDialog(self.auth_service)
            if setup_dlg.exec() != QDialog.Accepted:
                return 1

        # Login loop - allows returning to login after logout
        while True:
            # Show login dialog
            login_dlg = LoginDialog(self.auth_service)
            if login_dlg.exec() != QDialog.Accepted or not login_dlg.authenticated:
                return 0  # User cancelled login

            # Launch main window with all services
            self.main_window = MainWindow(
                self.job_service, 
                self.export_service, 
                self.backup_service,
                self.auth_service,
                self.attachment_service
            )
            self.main_window.show()
            self.app.exec()
            
            # Check if user logged out (vs just closing window)
            if not self.main_window.was_logout_requested():
                break  # Normal close, exit app
            
            # User logged out, loop back to login dialog
        
        return 0
