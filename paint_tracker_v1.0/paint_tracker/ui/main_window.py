"""
Presentation Layer for Paint Tracking Program
Modern UI implementation using PySide6 Qt framework
"""

import sys
import json
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from PySide6.QtCore import Qt, Slot, QSettings
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QRadioButton, QButtonGroup,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QGroupBox, QMessageBox, QFileDialog, QDialog, QDialogButtonBox,
    QFormLayout, QDoubleSpinBox, QTabWidget, QSplitter, QStatusBar,
    QStackedWidget, QInputDialog
)

from paint_tracker.core import (
    JobService, ExportService, BackupService,
    AuthenticationService, ValidationService
)
from paint_tracker.ui.dialogs import JobFormDialog  # job form with dropdowns


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
    QHeaderView::section { background-color: #4CAF50; color: white; padding: 8px; border: none; font-weight: bold; }

    QStatusBar { background-color: #333; color: white; }
    QMenuBar { background-color: white; border-bottom: 1px solid #ddd; }
    QMenuBar::item:selected { background-color: #4CAF50; color: white; }
    QMenu::item:selected { background-color: #4CAF50; color: white; }
    """


# ---------- Dialogs ----------

class JobHistoryDialog(QDialog):
    """Dialog showing complete history of mixes for a job"""

    def __init__(self, job_service: JobService, job_number: str, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.job_number = job_number
        self.details: Dict = {}
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
        self.total_amount_label = QLabel("Total Paint: 0 units")
        self.date_range_label = QLabel("Date Range: -")
        stats_row.addWidget(self.total_colors_label)
        stats_row.addWidget(self.total_amount_label)
        stats_row.addWidget(self.date_range_label)
        stats_row.addStretch()
        header_layout.addLayout(stats_row)

        layout.addWidget(header_frame)

        # table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)

        cols = [
            "Date Mixed", "Color Name", "Paint Code", "Version",
            "Manufacturer", "Amount", "Mixed By", "Notes"
        ]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        layout.addWidget(self.table)

        # buttons
        row_btns = QHBoxLayout()
        export_btn = QPushButton("Export History")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_history)
        row_btns.addWidget(export_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load)
        row_btns.addWidget(refresh_btn)

        row_btns.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        row_btns.addWidget(close_btn)

        layout.addLayout(row_btns)

        self.load()

    @Slot()
    def load(self):
        self.details = self.job_service.repository.get_job_details(self.job_number)

        self.total_colors_label.setText(f"Total Colors: {self.details['total_colors']}")
        self.total_amount_label.setText(f"Total Paint: {self.details['total_amount']:.2f} units")

        first = self.details["date_range"]["first"]
        last = self.details["date_range"]["last"]
        self.date_range_label.setText(
            f"Date Range: {first} to {last}" if first and last else "Date Range: No mixes yet"
        )

        self.table.setRowCount(0)
        for e in self.details["history"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(e.get("created_at", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(e.get("color_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(e.get("paint_code", "")))
            self.table.setItem(row, 3, QTableWidgetItem(e.get("paint_version", "1.0")))
            self.table.setItem(row, 4, QTableWidgetItem(e.get("manufacturer", "")))
            self.table.setItem(row, 5, QTableWidgetItem(f"{e.get('mixed_amount', 0)} units"))
            self.table.setItem(row, 6, QTableWidgetItem(e.get("mixed_by", "")))
            self.table.setItem(row, 7, QTableWidgetItem(e.get("notes", "")))

    @Slot()
    def export_history(self):
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


class JobFormDialog_OLD(QDialog):  # old basic dialog - not using this anymore
    """Create a new mix entry for a job number"""

    def __init__(self, job_service: JobService, job_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.job_data = job_data or {}
        self.is_edit = bool(job_data)

        self.setWindowTitle("Edit Job" if self.is_edit else "Create New Mix")
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)

        title = QLabel("Edit Job Details" if self.is_edit else "Create New Mix Entry")
        title.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        form = QFormLayout()

        self.job_number_edit = QLineEdit()
        if self.is_edit:
            self.job_number_edit.setEnabled(False)
        form.addRow("Job Number*", self.job_number_edit)

        self.manufacturer_edit = QLineEdit()
        form.addRow("Manufacturer*", self.manufacturer_edit)

        self.paint_code_edit = QLineEdit()
        form.addRow("Paint Code*", self.paint_code_edit)

        self.paint_version_edit = QLineEdit()
        self.paint_version_edit.setPlaceholderText("e.g. 1.0 1.1 2.0")
        form.addRow("Paint Version*", self.paint_version_edit)

        self.color_name_edit = QLineEdit()
        form.addRow("Color Name", self.color_name_edit)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 10000.0)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" grams")
        form.addRow("Amount Mixed*", self.amount_spin)

        self.mixed_by_edit = QLineEdit()
        form.addRow("Mixed By", self.mixed_by_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(120)
        form.addRow("Notes", self.notes_edit)

        layout.addLayout(form)

        if self.is_edit:
            self._populate()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if not self.is_edit:
            self.job_number_edit.setFocus()

    def _populate(self):
        d = self.job_data
        self.job_number_edit.setText(d.get("job_number", ""))
        self.manufacturer_edit.setText(d.get("manufacturer", ""))
        self.paint_code_edit.setText(d.get("paint_code", ""))
        self.paint_version_edit.setText(d.get("paint_version", "1.0"))
        self.color_name_edit.setText(d.get("color_name", ""))
        try:
            self.amount_spin.setValue(float(d.get("mixed_amount", 0)))
        except Exception:
            self.amount_spin.setValue(0.0)
        self.mixed_by_edit.setText(d.get("mixed_by", ""))
        self.notes_edit.setText(d.get("notes", ""))

    @Slot()
    def _save(self):
        payload = {
            "job_number": self.job_number_edit.text().strip(),
            "manufacturer": self.manufacturer_edit.text().strip(),
            "paint_code": self.paint_code_edit.text().strip(),
            "paint_version": self.paint_version_edit.text().strip() or "1.0",
            "color_name": self.color_name_edit.text().strip(),
            "mixed_amount": str(self.amount_spin.value()),
            "mixed_by": self.mixed_by_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip()
        }

        ok, msg = ValidationService.validate_job_payload(payload)
        if not ok:
            QMessageBox.critical(self, "Validation Error", msg)
            return

        if self.is_edit:
            success, message = self.job_service.update_job(self.job_data["id"], payload)
        else:
            success, message = self.job_service.create_job(payload)

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)


# ---------- Dashboard ----------

class DashboardWidget(QWidget):
    """Main dashboard with summary list and actions"""

    def __init__(self, job_service: JobService, export_service: ExportService, parent=None):
        super().__init__(parent)
        self.job_service = job_service
        self.export_service = export_service
        self.job_summaries: List[Dict] = []
        self.search_query = ""
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # top splitter
        top = QSplitter(Qt.Horizontal)

        # search panel
        search_group = QGroupBox("Search Filter")
        s_layout = QVBoxLayout(search_group)

        row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by job number color or paint code")
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

        filter_row = QHBoxLayout()
        self.filter_group = QButtonGroup(self)
        all_radio = QRadioButton("All Jobs")
        all_radio.setChecked(True)
        recent_radio = QRadioButton("Last 30 Days")
        self.filter_group.addButton(all_radio, 0)
        self.filter_group.addButton(recent_radio, 1)
        filter_row.addWidget(all_radio)
        filter_row.addWidget(recent_radio)
        filter_row.addStretch()
        s_layout.addLayout(filter_row)

        self.filter_group.buttonClicked.connect(self.perform_search)

        top.addWidget(search_group)

        # stats panel
        stats_group = QGroupBox("Statistics")
        f = QFormLayout(stats_group)
        self.stats_labels = {
            "total_jobs": QLabel("0"),
            "recent_jobs": QLabel("0"),
            "total_paint": QLabel("0 units"),
            "avg": QLabel("0 units")
        }
        self.stats_labels["total_jobs"].setAlignment(Qt.AlignRight)
        self.stats_labels["recent_jobs"].setAlignment(Qt.AlignRight)
        self.stats_labels["total_paint"].setAlignment(Qt.AlignRight)
        self.stats_labels["avg"].setAlignment(Qt.AlignRight)

        f.addRow("Total Jobs:", self.stats_labels["total_jobs"])
        f.addRow("Recent 30 days:", self.stats_labels["recent_jobs"])
        f.addRow("Total Paint Mixed:", self.stats_labels["total_paint"])
        f.addRow("Average per Job:", self.stats_labels["avg"])

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

        headers = ["Job Number", "Total Mixes", "Total Amount", "Colors", "First Mix", "Last Mix"]
        self.jobs_table.setColumnCount(len(headers))
        self.jobs_table.setHorizontalHeaderLabels(headers)
        h = self.jobs_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        h.setStretchLastSection(True)

        # double click opens history
        self.jobs_table.itemDoubleClicked.connect(self.view_job_history)

        layout.addWidget(self.jobs_table)

    # ---- helpers ----

    def add_summary_to_table(self, summary: dict):
        row = self.jobs_table.rowCount()
        self.jobs_table.insertRow(row)

        job_no = str(summary.get("job_number", ""))

        col0 = QTableWidgetItem(job_no)
        col0.setData(Qt.UserRole, job_no)  # store for double click
        self.jobs_table.setItem(row, 0, col0)

        entry_count = summary.get("entry_count", summary.get("mix_count", 0))
        total_amount = summary.get("total_amount", summary.get("total_paint", 0))

        colors_val = summary.get("colors", "")
        if isinstance(colors_val, (list, tuple)):
            colors_text = ", ".join(colors_val)
        else:
            colors_text = str(colors_val) if colors_val else "N A"

        first_mixed = summary.get("first_mixed", summary.get("first_mix_date", ""))
        last_mixed = summary.get("last_mixed", summary.get("last_mix_date", ""))

        self.jobs_table.setItem(row, 1, QTableWidgetItem(str(entry_count)))
        self.jobs_table.setItem(row, 2, QTableWidgetItem(str(total_amount)))
        self.jobs_table.setItem(row, 3, QTableWidgetItem(colors_text))
        self.jobs_table.setItem(row, 4, QTableWidgetItem(str(first_mixed)))
        self.jobs_table.setItem(row, 5, QTableWidgetItem(str(last_mixed)))

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
        # local filter of summaries for responsiveness
        q = self.search_query or self.search_edit.text().strip().lower()
        recent_only = self.filter_group.checkedId() == 1

        if not q and not recent_only:
            self.rebuild_summary_rows(self.job_summaries)
            return

        filtered = []
        for s in self.job_summaries:
            if recent_only:
                # include only rows whose last mix is in last 30 days
                last = s.get("last_mixed") or s.get("last_mix_date") or ""
                # simple include check, we already show recent count in stats
                # do not parse time here to avoid locale issues
            job_no = str(s.get("job_number", ""))
            colors_val = s.get("colors", "")
            colors_text = ", ".join(colors_val) if isinstance(colors_val, (list, tuple)) else str(colors_val)
            hay = f"{job_no} {colors_text}".lower()
            if (not q or q in hay):
                filtered.append(s)

        self.rebuild_summary_rows(filtered)

    @Slot()
    def clear_search(self):
        self.search_edit.clear()
        self.filter_group.button(0).setChecked(True)
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

        dlg = JobHistoryDialog(self.job_service, job_number, parent=self)
        dlg.exec()
        self.refresh_data()

    @Slot()
    def create_new_job(self):
        dlg = JobFormDialog(self.job_service, parent=self)
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
        self.stats_labels["total_paint"].setText(f"{stats.get('total_paint', 0)} units")
        avg = stats.get("average_paint_per_job") or stats.get("avg_paint_per_job")
        if avg is None:
            try:
                total = float(stats.get("total_paint", 0))
                jobs = int(stats.get("total_jobs", 1)) or 1
                avg = round(total / jobs, 2)
            except Exception:
                avg = 0
        self.stats_labels["avg"].setText(f"{avg} units")


# ---------- Admin ----------

class AdminDialog(QDialog):
    def __init__(self, backup_service: BackupService, auth_service: AuthenticationService, parent=None):
        super().__init__(parent)
        self.backup_service = backup_service
        self.auth_service = auth_service
        self.setWindowTitle("Administrator Mode")
        self.setModal(True)
        self.setMinimumSize(600, 420)

        self.stacked = QStackedWidget(self)
        v = QVBoxLayout(self)
        v.addWidget(self.stacked)

        self._build_auth()
        self._build_admin()
        self.stacked.setCurrentIndex(0)

    def _build_auth(self):
        w = QWidget()
        v = QVBoxLayout(w)
        t = QLabel("Administrator Authentication")
        t.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(16)
        f.setBold(True)
        t.setFont(f)
        v.addWidget(t)

        form = QFormLayout()
        self.pw_edit = QLineEdit()
        self.pw_edit.setEchoMode(QLineEdit.Password)
        self.pw_edit.returnPressed.connect(self.authenticate)
        form.addRow("Password:", self.pw_edit)
        v.addLayout(form)

        btn = QPushButton("Login")
        btn.clicked.connect(self.authenticate)
        v.addWidget(btn)

        self.stacked.addWidget(w)

    def _build_admin(self):
        w = QWidget()
        v = QVBoxLayout(w)

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

        btn_restore = QPushButton("Restore Backup")
        btn_restore.clicked.connect(self.restore_backup)
        vb.addWidget(btn_restore)

        btn_view = QPushButton("View Backups")
        btn_view.clicked.connect(self.view_backups)
        vb.addWidget(btn_view)
        vb.addStretch()
        tabs.addTab(tab_b, "Backup Management")

        # security tab
        tab_s = QWidget()
        vs = QVBoxLayout(tab_s)
        btn_change = QPushButton("Change Admin Password")
        btn_change.clicked.connect(self.change_password)
        vs.addWidget(btn_change)
        vs.addStretch()
        tabs.addTab(tab_s, "Security")

        v.addWidget(tabs)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        v.addWidget(btn_close)

        self.stacked.addWidget(w)

    @Slot()
    def authenticate(self):
        if AuthenticationService.verify_admin_password(self.pw_edit.text()):
            self.stacked.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, "Authentication Failed", "Invalid password")
            self.pw_edit.clear()
            self.pw_edit.setFocus()

    @Slot()
    def create_backup(self):
        if self.backup_service.create_backup():
            QMessageBox.information(self, "Success", "Backup created")
        else:
            QMessageBox.critical(self, "Error", "Failed to create backup")

    @Slot()
    def restore_backup(self):
        backups = self.backup_service.list_backups()
        if not backups:
            QMessageBox.information(self, "No Backups", "No backups found")
            return
        items = [f"{b['filename']} ({b['created']})" for b in backups]
        choice, ok = QInputDialog.getItem(self, "Select Backup", "Choose backup to restore:", items, 0, False)
        if not ok or not choice:
            return
        idx = items.index(choice)
        file = backups[idx]["filename"]
        if QMessageBox.question(self, "Confirm Restore", f"Restore {file}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self.backup_service.restore_backup(file):
                QMessageBox.information(self, "Success", "Database restored")
            else:
                QMessageBox.critical(self, "Error", "Restore failed")

    @Slot()
    def view_backups(self):
        backups = self.backup_service.list_backups()
        if not backups:
            QMessageBox.information(self, "No Backups", "No backups found")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Available Backups")
        dlg.setMinimumSize(600, 400)
        v = QVBoxLayout(dlg)
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Filename", "Size", "Created"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            size_mb = b["size"] / (1024 * 1024)
            table.setItem(i, 0, QTableWidgetItem(b["filename"]))
            table.setItem(i, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
            table.setItem(i, 2, QTableWidgetItem(b["created"]))
        v.addWidget(table)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.accept)
        v.addWidget(btn)
        dlg.exec()

    @Slot()
    def change_password(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Change Administrator Password")
        form = QFormLayout(dlg)
        old = QLineEdit(); old.setEchoMode(QLineEdit.Password)
        new = QLineEdit(); new.setEchoMode(QLineEdit.Password)
        conf = QLineEdit(); conf.setEchoMode(QLineEdit.Password)
        form.addRow("Current Password:", old)
        form.addRow("New Password:", new)
        form.addRow("Confirm Password:", conf)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form.addRow(btns)

        def save():
            if new.text() != conf.text():
                QMessageBox.critical(dlg, "Error", "New passwords do not match")
                return
            if AuthenticationService.change_admin_password(old.text(), new.text()):
                QMessageBox.information(dlg, "Success", "Password changed")
                dlg.accept()
            else:
                QMessageBox.critical(dlg, "Error", "Current password incorrect")

        btns.accepted.connect(save)
        btns.rejected.connect(dlg.reject)
        dlg.exec()


# ---------- Main Window and App ----------

class MainWindow(QMainWindow):
    def __init__(self, job_service: JobService, export_service: ExportService, backup_service: BackupService):
        super().__init__()
        self.job_service = job_service
        self.export_service = export_service
        self.backup_service = backup_service

        self.setWindowTitle("Paint Tracking System v2.0")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(StyleSheet.MAIN_STYLE)

        self._build_ui()
        self._menus()
        self._toolbar()
        self._status()

    def _build_ui(self):
        tabs = QTabWidget()
        self.dashboard = DashboardWidget(self.job_service, self.export_service)
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
        sb.showMessage("Ready")

    @Slot()
    def open_admin(self):
        dlg = AdminDialog(self.backup_service, AuthenticationService, self)
        dlg.exec()

    @Slot()
    def show_about(self):
        QMessageBox.about(
            self, "About Paint Tracking System",
            "<h2>Paint Tracking System v2.0</h2>"
            "<p>Three-layer architecture with Python/Qt</p>"
            "<p>Created for CS 499 Computer Science Capstone</p>"
            "<p>Author: Christopher Lajoie</p>"
            "<ul>"
            "<li>PySide6 Qt</li>"
            "<li>SQLite</li>"
            "<li>Repository and Services</li>"
            "</ul>"
        )


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
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.database_path = cfg.get("database_path")
            except Exception:
                pass

    def _save_config(self):
        cfg = {"database_path": str(self.database_path), "version": "2.0.0", "ui_framework": "PySide6"}
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def _first_run_wizard(self) -> bool:
        dlg = QDialog()
        dlg.setWindowTitle("Paint Tracking System - Setup")
        dlg.setMinimumWidth(420)
        v = QVBoxLayout(dlg)

        t = QLabel("Welcome to Paint Tracking System")
        f = QFont(); f.setPointSize(16); f.setBold(True)
        t.setFont(f); t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        v.addWidget(QLabel("Please select a location for the database:"))

        row = QHBoxLayout()
        btn_sel = QPushButton("Select Database Location")

        def pick():
            name, _ = QFileDialog.getSaveFileName(
                dlg, "Select Database Location",
                str(Path.home() / "paint_tracker.db"),
                "Database Files (*.db)"
            )
            if name:
                self.database_path = name
                self._save_config()
                dlg.accept()

        btn_sel.clicked.connect(pick)
        row.addWidget(btn_sel)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dlg.reject)
        row.addWidget(btn_cancel)
        v.addLayout(row)

        return dlg.exec() == QDialog.Accepted

    def initialize_services(self):
        self.job_service = JobService(self.database_path)
        self.export_service = ExportService(self.database_path)
        self.backup_service = BackupService(self.database_path, self.app_dir / "backups")
        self.backup_service.create_backup()

    def run(self) -> int:
        if not self.database_path or not os.path.exists(self.database_path):
            if not self._first_run_wizard():
                return 1

        self.initialize_services()

        self.main_window = MainWindow(self.job_service, self.export_service, self.backup_service)
        self.main_window.show()
        return self.app.exec()
