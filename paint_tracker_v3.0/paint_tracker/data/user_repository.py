"""
User Repository - Database operations for user accounts
Stores usernames, password hashes, and roles.

Author: Christopher Lajoie
"""

import sqlite3
from typing import List, Dict, Tuple, Optional
from datetime import datetime

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class UserRepository:
    """SQLite database operations for user accounts and authentication."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.ensure_schema()

    def ensure_schema(self) -> None:
        """Create users table and indexes if they don't exist"""
        cur = self._conn.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
            is_active INTEGER NOT NULL DEFAULT 1,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login TEXT
        )
        """)
        
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username 
        ON users(username)
        """)
        
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_role 
        ON users(role)
        """)
        
        self._conn.commit()

    def create_user(self, username: str, password_hash: str, role: str = 'user') -> Tuple[bool, str]:
        """
        Create a new user with hashed password.
        
        Args:
            username: Unique username (case-insensitive)
            password_hash: bcrypt hashed password
            role: 'admin' or 'user'
            
        Returns:
            Tuple of (success, message)
        """
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                INSERT INTO users (username, password_hash, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username.strip(), password_hash, role, now, now))
            self._conn.commit()
            return True, f"User '{username}' created successfully"
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' already exists"
        except Exception as e:
            return False, f"Failed to create user: {e}"

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Retrieve user by username for authentication.
        
        Args:
            username: The username to look up
            
        Returns:
            User dict or None if not found
        """
        cur = self._conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, role, is_active, 
                   failed_attempts, locked_until, created_at, last_login
            FROM users
            WHERE username = ? COLLATE NOCASE
        """, (username.strip(),))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Retrieve user by ID"""
        cur = self._conn.cursor()
        cur.execute("""
            SELECT id, username, role, is_active, created_at, last_login
            FROM users
            WHERE id = ?
        """, (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_password(self, user_id: int, new_password_hash: str) -> Tuple[bool, str]:
        """Update user's password hash"""
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                UPDATE users
                SET password_hash = ?, updated_at = ?
                WHERE id = ?
            """, (new_password_hash, now, user_id))
            self._conn.commit()
            return True, "Password updated successfully"
        except Exception as e:
            return False, f"Failed to update password: {e}"

    def update_last_login(self, user_id: int) -> None:
        """Record successful login timestamp"""
        now = datetime.now().isoformat(timespec="seconds")
        self._conn.execute("""
            UPDATE users
            SET last_login = ?, failed_attempts = 0, locked_until = NULL
            WHERE id = ?
        """, (now, user_id))
        self._conn.commit()

    def increment_failed_attempts(self, user_id: int) -> int:
        """
        Increment failed login counter and optionally lock account.
        
        Returns:
            Current failed attempt count
        """
        cur = self._conn.cursor()
        cur.execute("SELECT failed_attempts FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return 0
        
        new_count = row["failed_attempts"] + 1
        
        locked_until = None
        if new_count >= MAX_LOGIN_ATTEMPTS:
            from datetime import timedelta
            locked_until = (datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat(timespec="seconds")
        
        self._conn.execute("""
            UPDATE users
            SET failed_attempts = ?, locked_until = ?
            WHERE id = ?
        """, (new_count, locked_until, user_id))
        self._conn.commit()
        
        return new_count

    def is_account_locked(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if account is currently locked.
        
        Returns:
            Tuple of (is_locked, locked_until_time)
        """
        cur = self._conn.cursor()
        cur.execute("SELECT locked_until FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        
        if not row or not row["locked_until"]:
            return False, None
        
        locked_until = datetime.fromisoformat(row["locked_until"])
        if datetime.now() < locked_until:
            return True, row["locked_until"]
        
        # Lock expired, reset
        self._conn.execute("""
            UPDATE users
            SET locked_until = NULL, failed_attempts = 0
            WHERE id = ?
        """, (user_id,))
        self._conn.commit()
        return False, None

    def set_user_active(self, user_id: int, is_active: bool) -> Tuple[bool, str]:
        """Enable or disable a user account"""
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                UPDATE users
                SET is_active = ?, updated_at = ?
                WHERE id = ?
            """, (1 if is_active else 0, now, user_id))
            self._conn.commit()
            status = "activated" if is_active else "deactivated"
            return True, f"User {status} successfully"
        except Exception as e:
            return False, f"Failed to update user status: {e}"

    def update_role(self, user_id: int, new_role: str) -> Tuple[bool, str]:
        """Update user's role (admin/user)"""
        if new_role not in ('admin', 'user'):
            return False, "Invalid role. Must be 'admin' or 'user'"
        
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                UPDATE users
                SET role = ?, updated_at = ?
                WHERE id = ?
            """, (new_role, now, user_id))
            self._conn.commit()
            return True, f"Role updated to '{new_role}'"
        except Exception as e:
            return False, f"Failed to update role: {e}"

    def get_all_users(self) -> List[Dict]:
        """Get all users for admin management (excludes password hashes)"""
        cur = self._conn.cursor()
        cur.execute("""
            SELECT id, username, role, is_active, created_at, last_login
            FROM users
            ORDER BY username COLLATE NOCASE
        """)
        return [dict(row) for row in cur.fetchall()]

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete a user (admin function)"""
        try:
            cur = self._conn.cursor()
            cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                return False, "User not found"
            
            username = row["username"]
            self._conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self._conn.commit()
            return True, f"User '{username}' deleted"
        except Exception as e:
            return False, f"Failed to delete user: {e}"

    def user_count(self) -> int:
        """Get total number of users"""
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM users")
        return cur.fetchone()["count"]

    def has_admin(self) -> bool:
        """Check if at least one admin user exists"""
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
        return cur.fetchone()["count"] > 0

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
