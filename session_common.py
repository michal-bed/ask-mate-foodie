from flask import session, redirect
from functools import wraps


def require_login(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'login' in session:
            return function(*args, **kwargs)
        return redirect("/login")
    return wrapper
