"""
Login Dialog - Presentation Layer for User Authentication
UI components for login, initial setup, password change, and user registration.

Author: Christopher Lajoie
"""

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFormLayout, QMessageBox,
    QGroupBox, QCheckBox
)


class BaseAuthDialog(QDialog):
    """Base class for authentication dialogs with common functionality"""
    
    def _show_error(self, message):
        """Display error message in status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")


class LoginDialog(BaseAuthDialog):
    """Login dialog shown at application startup"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.authenticated = False
        
        self.setWindowTitle("Paint Tracking System - Login")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header = QLabel("Paint Tracking System")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Please log in to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # Login form
        form_group = QGroupBox("Credentials")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setValidator(QRegularExpressionValidator(
            QRegularExpression(r'^[a-zA-Z0-9_]+$'), self))
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(35)
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setMinimumHeight(35)
        form_layout.addRow("Password:", self.password_input)

        # Show password checkbox
        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.toggled.connect(self._toggle_password_visibility)
        form_layout.addRow("", self.show_password_cb)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_btn.clicked.connect(self._handle_login)
        button_layout.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("Exit")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Connect Enter key to login
        self.username_input.returnPressed.connect(self._focus_password)
        self.password_input.returnPressed.connect(self._handle_login)

        # Focus username field
        self.username_input.setFocus()

    def _toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def _focus_password(self):
        self.password_input.setFocus()

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self._show_error("Please enter a username")
            self.username_input.setFocus()
            return

        if not password:
            self._show_error("Please enter a password")
            self.password_input.setFocus()
            return

        # Attempt authentication
        success, message = self.auth_service.authenticate(username, password)
        
        if success:
            self.authenticated = True
            self.accept()
        else:
            self._show_error(message)
            self.password_input.clear()
            self.password_input.setFocus()


class InitialSetupDialog(BaseAuthDialog):
    """Dialog for creating the first admin user"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setup_complete = False
        
        self.setWindowTitle("Paint Tracking System - Initial Setup")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header = QLabel("Welcome to Paint Tracking System")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        info = QLabel("Create your administrator account to get started.")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        layout.addSpacing(10)

        # Admin creation form
        form_group = QGroupBox("Administrator Account")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setValidator(QRegularExpressionValidator(
            QRegularExpression(r'^[a-zA-Z0-9_]+$'), self))
        self.username_input.setPlaceholderText("Choose a username")
        self.username_input.setMinimumHeight(35)
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Choose a strong password")
        self.password_input.setMinimumHeight(35)
        form_layout.addRow("Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setMinimumHeight(35)
        form_layout.addRow("Confirm:", self.confirm_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Password requirements
        req_group = QGroupBox("Password Requirements")
        req_layout = QVBoxLayout()
        requirements = [
            "• At least 8 characters",
            "• One uppercase letter (A-Z)",
            "• One lowercase letter (a-z)",
            "• One digit (0-9)",
            "• One special character (!@#$%^&*)"
        ]
        for req in requirements:
            label = QLabel(req)
            label.setStyleSheet("color: #666; font-size: 11px;")
            req_layout.addWidget(label)
        req_group.setLayout(req_layout)
        layout.addWidget(req_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("Create Account")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.create_btn.clicked.connect(self._handle_create)
        button_layout.addWidget(self.create_btn)

        self.cancel_btn = QPushButton("Exit")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Connect Enter key
        self.confirm_input.returnPressed.connect(self._handle_create)

    def _handle_create(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not username:
            self._show_error("Please enter a username")
            return

        if not password:
            self._show_error("Please enter a password")
            return

        if password != confirm:
            self._show_error("Passwords do not match")
            self.confirm_input.clear()
            self.confirm_input.setFocus()
            return

        # Attempt to create admin
        success, message = self.auth_service.setup_initial_admin(username, password)
        
        if success:
            self.setup_complete = True
            QMessageBox.information(
                self, "Success",
                f"Administrator account '{username}' created successfully!\n\n"
                "Please log in with your new credentials."
            )
            self.accept()
        else:
            self._show_error(message)


class ChangePasswordDialog(BaseAuthDialog):
    """Dialog for changing user's password"""

    def __init__(self, auth_service, user_id, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.user_id = user_id
        
        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_group = QGroupBox("Change Password")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.Password)
        self.current_input.setMinimumHeight(35)
        form_layout.addRow("Current Password:", self.current_input)

        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.Password)
        self.new_input.setMinimumHeight(35)
        form_layout.addRow("New Password:", self.new_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(35)
        form_layout.addRow("Confirm New:", self.confirm_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Change Password")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._handle_change)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    def _handle_change(self):
        current = self.current_input.text()
        new_pwd = self.new_input.text()
        confirm = self.confirm_input.text()

        if not current:
            self._show_error("Please enter your current password")
            return

        if not new_pwd:
            self._show_error("Please enter a new password")
            return

        if new_pwd != confirm:
            self._show_error("New passwords do not match")
            return

        success, message = self.auth_service.change_password(
            self.user_id, current, new_pwd
        )
        
        if success:
            QMessageBox.information(self, "Success", "Password changed successfully!")
            self.accept()
        else:
            self._show_error(message)


class CreateUserDialog(BaseAuthDialog):
    """Dialog for admin to create new users"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        
        self.setWindowTitle("Create New User")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_group = QGroupBox("New User Details")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setValidator(QRegularExpressionValidator(
            QRegularExpression(r'^[a-zA-Z0-9_]+$'), self))
        self.username_input.setMinimumHeight(35)
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        form_layout.addRow("Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(35)
        form_layout.addRow("Confirm:", self.confirm_input)

        # Role checkbox
        self.admin_cb = QCheckBox("Grant administrator privileges")
        form_layout.addRow("", self.admin_cb)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("Create User")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.clicked.connect(self._handle_create)
        button_layout.addWidget(self.create_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    def _handle_create(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        role = 'admin' if self.admin_cb.isChecked() else 'user'

        if not username:
            self._show_error("Please enter a username")
            return

        if not password:
            self._show_error("Please enter a password")
            return

        if password != confirm:
            self._show_error("Passwords do not match")
            return

        success, message = self.auth_service.create_user(username, password, role)
        
        if success:
            QMessageBox.information(
                self, "Success",
                f"User '{username}' created successfully!"
            )
            self.accept()
        else:
            self._show_error(message)
