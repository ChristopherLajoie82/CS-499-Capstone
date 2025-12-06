"""
Authentication Service
Handles login, password hashing with bcrypt, and user sessions.

Author: Christopher Lajoie
"""

import re
from typing import Tuple, Optional, Dict
from paint_tracker.data.repository_factory import RepositoryFactory
from paint_tracker.data.user_repository import MAX_LOGIN_ATTEMPTS


class AuthenticationService:
    """
    Handles user login and password management.
    Uses bcrypt for secure password hashing.
    """

    def __init__(self):
        self.user_repo = RepositoryFactory.create_user_repository()
        self._current_user: Optional[Dict] = None
        self._bcrypt_available = self._check_bcrypt()

    def _check_bcrypt(self) -> bool:
        """Check if bcrypt is available"""
        try:
            import bcrypt
            return True
        except ImportError:
            return False

    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with automatic salt generation.
        
        bcrypt automatically handles:
        - Salt generation (random per password)
        - Work factor (cost factor for computational difficulty)
        - Salt storage (embedded in the hash)
        """
        if self._bcrypt_available:
            import bcrypt
            # Work factor of 12 is recommended for 2024
            # This creates ~250ms delay per hash on modern hardware
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        else:
            # Fallback for systems without bcrypt (not recommended for production)
            import hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against stored hash using constant-time comparison.
        
        bcrypt.checkpw uses constant-time comparison to prevent timing attacks.
        """
        if self._bcrypt_available:
            import bcrypt
            try:
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    password_hash.encode('utf-8')
                )
            except Exception:
                return False
        else:
            # Fallback verification
            import hashlib
            import hmac
            test_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return hmac.compare_digest(test_hash, password_hash)

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements.
        
        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password meets requirements"

    def validate_username(self, username: str) -> Tuple[bool, str]:
        """Validate username format"""
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 50:
            return False, "Username must be 50 characters or less"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, "Valid username"

    def create_user(self, username: str, password: str, role: str = 'user') -> Tuple[bool, str]:
        """
        Create a new user with validated credentials.
        
        Args:
            username: Desired username
            password: Plain text password (will be hashed)
            role: 'admin' or 'user'
            
        Returns:
            Tuple of (success, message)
        """
        valid, msg = self.validate_username(username)
        if not valid:
            return False, msg
        
        valid, msg = self.validate_password_strength(password)
        if not valid:
            return False, msg
        
        password_hash = self._hash_password(password)
        return self.user_repo.create_user(username, password_hash, role)

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            Tuple of (success, message)
        """
        user = self.user_repo.get_user_by_username(username)
        
        if not user:
            return False, "Invalid username or password"
        
        if not user.get('is_active'):
            return False, "Account is disabled. Contact administrator."
        
        is_locked, locked_until = self.user_repo.is_account_locked(user['id'])
        if is_locked:
            return False, f"Account locked until {locked_until}. Too many failed attempts."
        
        if not self._verify_password(password, user['password_hash']):
            attempts = self.user_repo.increment_failed_attempts(user['id'])
            remaining = MAX_LOGIN_ATTEMPTS - attempts
            if remaining > 0:
                return False, f"Invalid username or password. {remaining} attempts remaining."
            else:
                return False, "Account locked due to too many failed attempts."
        
        self.user_repo.update_last_login(user['id'])
        
        self._current_user = {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
        
        return True, f"Welcome, {user['username']}!"

    def logout(self) -> None:
        """Clear current user session"""
        self._current_user = None

    def get_current_user(self) -> Optional[Dict]:
        """Get currently logged in user"""
        return self._current_user

    def is_authenticated(self) -> bool:
        """Check if a user is currently logged in"""
        return self._current_user is not None

    def is_admin(self) -> bool:
        """Check if current user has admin role"""
        if not self._current_user:
            return False
        return self._current_user.get('role') == 'admin'

    def require_admin(self) -> Tuple[bool, str]:
        """Check if current user can perform admin actions"""
        if not self.is_authenticated():
            return False, "Authentication required"
        if not self.is_admin():
            return False, "Administrator privileges required"
        return True, "Authorized"

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user's password with verification of old password.
        
        Args:
            user_id: ID of user changing password
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Tuple of (success, message)
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        full_user = self.user_repo.get_user_by_username(user['username'])
        
        if not self._verify_password(old_password, full_user['password_hash']):
            return False, "Current password is incorrect"
        
        valid, msg = self.validate_password_strength(new_password)
        if not valid:
            return False, msg
        
        if old_password == new_password:
            return False, "New password must be different from current password"
        
        new_hash = self._hash_password(new_password)
        return self.user_repo.update_password(user_id, new_hash)

    def admin_reset_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        """
        Admin function to reset a user's password without knowing the old one.
        
        Args:
            user_id: ID of user to reset
            new_password: New password to set
            
        Returns:
            Tuple of (success, message)
        """
        authorized, msg = self.require_admin()
        if not authorized:
            return False, msg
        
        valid, msg = self.validate_password_strength(new_password)
        if not valid:
            return False, msg
        
        new_hash = self._hash_password(new_password)
        return self.user_repo.update_password(user_id, new_hash)

    def setup_initial_admin(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Create the first admin user during initial setup.
        Only works if no admin exists yet.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Tuple of (success, message)
        """
        if self.user_repo.has_admin():
            return False, "An administrator already exists"
        
        return self.create_user(username, password, role='admin')

    def needs_initial_setup(self) -> bool:
        """Check if the system needs initial admin setup"""
        return self.user_repo.user_count() == 0

    def get_all_users(self):
        """Get all users for admin management"""
        return self.user_repo.get_all_users()

    def set_user_active(self, user_id: int, is_active: bool) -> Tuple[bool, str]:
        """Admin function to enable/disable user"""
        authorized, msg = self.require_admin()
        if not authorized:
            return False, msg
        return self.user_repo.set_user_active(user_id, is_active)

    def update_user_role(self, user_id: int, new_role: str) -> Tuple[bool, str]:
        """Admin function to change user role"""
        authorized, msg = self.require_admin()
        if not authorized:
            return False, msg
        return self.user_repo.update_role(user_id, new_role)

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Admin function to delete user"""
        authorized, msg = self.require_admin()
        if not authorized:
            return False, msg
        
        # Prevent self-deletion
        if self._current_user and self._current_user['id'] == user_id:
            return False, "Cannot delete your own account"
        
        return self.user_repo.delete_user(user_id)

    def bcrypt_status(self) -> str:
        """Return status of bcrypt availability"""
        if self._bcrypt_available:
            return "bcrypt available - using secure password hashing"
        else:
            return "bcrypt not installed - using SHA256 fallback (install bcrypt for production)"
