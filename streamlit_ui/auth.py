"""
Authentication Module for Streamlit UI

Multi-user authentication with role-based access control.
"""

import streamlit as st
import streamlit_authenticator as stauth
from typing import Dict, Optional, Tuple
import yaml
from pathlib import Path
import bcrypt

from streamlit_ui.config import AUTH_CONFIG, DEFAULT_USERS
from memory.schemas import UserRole


class AuthManager:
    """
    Manages user authentication and role-based access
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize auth manager

        Args:
            config_path: Path to user config file
        """
        self.config_path = config_path or "streamlit_ui/users.yaml"
        self.users = self._load_users()
        self.authenticator = None

    def _load_users(self) -> Dict:
        """Load users from config file or use defaults"""
        config_file = Path(self.config_path)

        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Use default users
            return {"credentials": {"usernames": DEFAULT_USERS}}

    def _save_users(self):
        """Save users to config file"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            yaml.dump(self.users, f)

    def initialize(self) -> stauth.Authenticate:
        """
        Initialize authenticator

        Returns:
            Authenticator instance
        """
        # Hash passwords if not already hashed
        credentials = self.users.get("credentials", {})
        usernames = credentials.get("usernames", {})

        # Convert to streamlit-authenticator format (v0.4.x)
        # In v0.4.x, the structure is different - use credentials dict directly
        auth_credentials = {
            "usernames": {}
        }

        for username, user_data in usernames.items():
            password = user_data.get("password", "")

            # Hash password if it's not already hashed (doesn't start with $2b$)
            if not password.startswith("$2b$"):
                hashed_password = bcrypt.hashpw(
                    password.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
            else:
                hashed_password = password

            auth_credentials["usernames"][username] = {
                "name": user_data.get("name", username),
                "password": hashed_password
            }

        self.authenticator = stauth.Authenticate(
            credentials=auth_credentials,
            cookie_name=AUTH_CONFIG["cookie_name"],
            key=AUTH_CONFIG["cookie_key"],
            cookie_expiry_days=AUTH_CONFIG["cookie_expiry_days"]
        )

        return self.authenticator

    def login(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Display login form and handle authentication

        Returns:
            Tuple of (name, username, authentication_status)
        """
        if self.authenticator is None:
            self.initialize()

        # In v0.4.x, login returns differently or modifies session state
        try:
            self.authenticator.login()
        except Exception as e:
            st.error(f"Login error: {e}")
            return None, None, None

        # Access authentication state from session state (v0.4.x stores it there)
        name = st.session_state.get("name")
        authentication_status = st.session_state.get("authentication_status")
        username = st.session_state.get("username")

        return name, username, authentication_status

    def logout(self):
        """Handle logout"""
        if self.authenticator:
            self.authenticator.logout("Logout", "sidebar")

    def get_user_role(self, username: str) -> UserRole:
        """
        Get user role

        Args:
            username: Username

        Returns:
            User role
        """
        users = self.users.get("credentials", {}).get("usernames", {})
        user_data = users.get(username, {})
        role_str = user_data.get("role", "viewer")

        try:
            return UserRole(role_str)
        except ValueError:
            return UserRole.VIEWER

    def has_permission(self, username: str, required_role: UserRole) -> bool:
        """
        Check if user has required permission

        Args:
            username: Username
            required_role: Required role level

        Returns:
            True if user has permission
        """
        user_role = self.get_user_role(username)

        # Role hierarchy: admin > tester > viewer
        role_levels = {
            UserRole.ADMIN: 3,
            UserRole.TESTER: 2,
            UserRole.VIEWER: 1
        }

        return role_levels.get(user_role, 0) >= role_levels.get(required_role, 0)

    def create_user(
        self,
        username: str,
        name: str,
        password: str,
        role: str = "viewer"
    ) -> bool:
        """
        Create new user (admin only)

        Args:
            username: Username
            name: Full name
            password: Password
            role: User role

        Returns:
            True if created successfully
        """
        users = self.users.get("credentials", {}).get("usernames", {})

        if username in users:
            return False

        users[username] = {
            "name": name,
            "password": password,  # Should be hashed in production
            "role": role
        }

        self._save_users()
        return True


def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if "authentication_status" not in st.session_state:
            st.warning("⚠️ Please login to continue")
            st.stop()

        if st.session_state["authentication_status"] != True:
            st.error("❌ Authentication failed")
            st.stop()

        return func(*args, **kwargs)

    return wrapper


def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "username" not in st.session_state:
                st.error("❌ Not authenticated")
                st.stop()

            auth_manager = AuthManager()
            if not auth_manager.has_permission(st.session_state["username"], required_role):
                st.error(f"❌ Requires {required_role.value} role or higher")
                st.stop()

            return func(*args, **kwargs)
        return wrapper
    return decorator
