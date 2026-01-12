"""
Authentication Service for Revolut Trading App
Handles user registration, login, and session management
"""

import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, g


class AuthService:
    """Handles authentication and authorization"""

    def __init__(self, db=None):
        self.db = db
        self.token_expiry_hours = 24

    def register_user(self, username, email, password):
        """Register a new user"""
        from models import User, db

        # Validate input
        if not username or len(username) < 3:
            return None, "Username must be at least 3 characters"

        if not email or '@' not in email:
            return None, "Invalid email address"

        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters"

        # Check if user exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"

        if User.query.filter_by(email=email).first():
            return None, "Email already registered"

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, f"Registration failed: {str(e)}"

    def login_user(self, username_or_email, password):
        """Authenticate user and return session token"""
        from models import User, db

        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user or not user.check_password(password):
            return None, "Invalid credentials"

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        return user, None

    def get_current_user(self):
        """Get the currently authenticated user from session"""
        from models import User

        user_id = session.get('user_id')
        if user_id:
            return User.query.get(user_id)
        return None

    def logout_user(self):
        """Logout the current user"""
        session.pop('user_id', None)


# Authentication decorator
def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models import User

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_optional():
    """Get current user if logged in, otherwise None"""
    from models import User
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


# Global auth service instance
auth_service = AuthService()
