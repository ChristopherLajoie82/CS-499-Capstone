"""
User Repository - PostgreSQL Data Access Layer for User Authentication
Handles user accounts, password storage, and role-based access for multi-user environment.

Author: Christopher Lajoie
CS 499 Enhancement Three: Database Enhancement
"""

import psycopg2
import psycopg2.extras
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class UserRepository:
    """
    PostgreSQL repository for user authentication data.
    Implements secure password storage and role-based access for multi-user support.
    """

    def __init__(self, connection_params: Dict[str, str]):
        """
        Initialize PostgreSQL connection.
        
        Args:
            connection_params: Dict with keys: host, port, database, user, password
        """
        self.connection_params = connection_params
        self._conn = None
        self._connect()
        self.ensure_schema()

    def _connect(self):
        """Establish database connection"""
        try:
            self._conn = psycopg2.connect(
                host=self.connection_params.get('host', 'localhost'),
                port=self.connection_params.get('port', 5432),
                database=self.connection_params['database'],
                user=self.connection_params['user'],
                password=self.connection_params['password'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            self._conn.autocommit = False
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def ensure_schema(self) -> None:
        """Create users table and indexes if they don't exist"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
                """)
                
                # Create case-insensitive unique index on username
                cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower
                ON users(LOWER(username))
                """)
                
                cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_role 
                ON users(role)
                """)
                
                self._conn.commit()
        except psycopg2.Error as e:
            self._conn.rollback()
            raise Exception(f"Schema creation failed: {e}")

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
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, password_hash, role, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username.strip(), password_hash, role, datetime.now(), datetime.now()))
                self._conn.commit()
                return True, f"User '{username}' created successfully"
        except psycopg2.IntegrityError:
            self._conn.rollback()
            return False, f"Username '{username}' already exists"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to create user: {e}"

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Retrieve user by username for authentication (case-insensitive).
        
        Args:
            username: The username to look up
            
        Returns:
            User dict or None if not found
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, password_hash, role, is_active, 
                           failed_attempts, locked_until, created_at, last_login
                    FROM users
                    WHERE LOWER(username) = LOWER(%s)
                """, (username.strip(),))
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    # Convert timestamps to ISO strings for compatibility
                    if result.get('created_at'):
                        result['created_at'] = result['created_at'].isoformat()
                    if result.get('last_login'):
                        result['last_login'] = result['last_login'].isoformat()
                    if result.get('locked_until'):
                        result['locked_until'] = result['locked_until'].isoformat()
                    return result
                return None
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user: {e}")

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Retrieve user by ID"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, role, is_active, created_at, last_login
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    if result.get('created_at'):
                        result['created_at'] = result['created_at'].isoformat()
                    if result.get('last_login'):
                        result['last_login'] = result['last_login'].isoformat()
                    return result
                return None
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user: {e}")

    def update_password(self, user_id: int, new_password_hash: str) -> Tuple[bool, str]:
        """Update user's password hash"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET password_hash = %s, updated_at = %s
                    WHERE id = %s
                """, (new_password_hash, datetime.now(), user_id))
                self._conn.commit()
                return True, "Password updated successfully"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to update password: {e}"

    def update_last_login(self, user_id: int) -> None:
        """Record successful login timestamp"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET last_login = %s, failed_attempts = 0, locked_until = NULL
                    WHERE id = %s
                """, (datetime.now(), user_id))
                self._conn.commit()
        except psycopg2.Error:
            self._conn.rollback()

    def increment_failed_attempts(self, user_id: int) -> int:
        """
        Increment failed login counter and optionally lock account.
        
        Returns:
            Current failed attempt count
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT failed_attempts FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return 0
                
                new_count = row["failed_attempts"] + 1
                
                locked_until = None
                if new_count >= MAX_LOGIN_ATTEMPTS:
                    locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
                
                cur.execute("""
                    UPDATE users
                    SET failed_attempts = %s, locked_until = %s
                    WHERE id = %s
                """, (new_count, locked_until, user_id))
                self._conn.commit()
                
                return new_count
        except psycopg2.Error:
            self._conn.rollback()
            return 0

    def is_account_locked(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if account is currently locked.
        
        Returns:
            Tuple of (is_locked, locked_until_time)
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT locked_until FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                
                if not row or not row["locked_until"]:
                    return False, None
                
                locked_until = row["locked_until"]
                if datetime.now() < locked_until:
                    return True, locked_until.isoformat()
                
                # Lock expired, reset
                cur.execute("""
                    UPDATE users
                    SET locked_until = NULL, failed_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                self._conn.commit()
                return False, None
        except psycopg2.Error:
            return False, None

    def set_user_active(self, user_id: int, is_active: bool) -> Tuple[bool, str]:
        """Enable or disable a user account"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET is_active = %s, updated_at = %s
                    WHERE id = %s
                """, (is_active, datetime.now(), user_id))
                self._conn.commit()
                status = "activated" if is_active else "deactivated"
                return True, f"User {status} successfully"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to update user status: {e}"

    def update_role(self, user_id: int, new_role: str) -> Tuple[bool, str]:
        """Update user's role (admin/user)"""
        if new_role not in ('admin', 'user'):
            return False, "Invalid role. Must be 'admin' or 'user'"
        
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET role = %s, updated_at = %s
                    WHERE id = %s
                """, (new_role, datetime.now(), user_id))
                self._conn.commit()
                return True, f"Role updated to '{new_role}'"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to update role: {e}"

    def get_all_users(self) -> List[Dict]:
        """Get all users for admin management (excludes password hashes)"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, role, is_active, created_at, last_login
                    FROM users
                    ORDER BY username
                """)
                users = []
                for row in cur.fetchall():
                    user = dict(row)
                    if user.get('created_at'):
                        user['created_at'] = user['created_at'].isoformat()
                    if user.get('last_login'):
                        user['last_login'] = user['last_login'].isoformat()
                    users.append(user)
                return users
        except psycopg2.Error as e:
            raise Exception(f"Failed to get users: {e}")

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete a user (admin function)"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return False, "User not found"
                
                username = row["username"]
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                self._conn.commit()
                return True, f"User '{username}' deleted"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to delete user: {e}"

    def user_count(self) -> int:
        """Get total number of users"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM users")
                return cur.fetchone()["count"]
        except psycopg2.Error:
            return 0

    def has_admin(self) -> bool:
        """Check if at least one admin user exists"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
                return cur.fetchone()["count"] > 0
        except psycopg2.Error:
            return False

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
