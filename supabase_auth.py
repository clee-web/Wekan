"""
Supabase Authentication Integration for Flask
Provides authentication using Supabase Auth instead of local password hashing
"""
from supabase_client import supabase
from flask import session, redirect, url_for

def supabase_signup(email, password, metadata=None):
    """
    Sign up a new user with Supabase Auth
    Returns: (success, data_or_error)
    """
    try:
        response = supabase.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': metadata or {}
            }
        })
        return True, response
    except Exception as e:
        return False, str(e)

def supabase_login(email, password):
    """
    Login a user with Supabase Auth
    Returns: (success, data_or_error)
    """
    try:
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        return True, response
    except Exception as e:
        return False, str(e)

def supabase_logout():
    """
    Logout the current user from Supabase
    Returns: (success, error_message)
    """
    try:
        supabase.auth.sign_out()
        session.clear()
        return True, None
    except Exception as e:
        return False, str(e)

def supabase_get_user():
    """
    Get the current authenticated user from Supabase
    Returns: (success, user_data_or_error)
    """
    try:
        user = supabase.auth.get_user()
        if user:
            return True, user
        return False, "No user logged in"
    except Exception as e:
        return False, str(e)

def supabase_reset_password(email):
    """
    Send a password reset email to the user
    Returns: (success, error_message)
    """
    try:
        supabase.auth.reset_password_email(email)
        return True, None
    except Exception as e:
        return False, str(e)

def supabase_update_password(new_password):
    """
    Update the current user's password
    Returns: (success, error_message)
    """
    try:
        supabase.auth.update_user({'password': new_password})
        return True, None
    except Exception as e:
        return False, str(e)

def supabase_login_required():
    """
    Decorator to check if user is authenticated with Supabase
    """
    def decorator(f):
        def wrapped(*args, **kwargs):
            success, user = supabase_get_user()
            if not success:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator
