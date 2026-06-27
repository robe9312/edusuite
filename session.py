_current_user = None
_permissions = []


def login(user):
    global _current_user, _permissions
    _current_user = user
    from db.database import get_role_permissions
    _permissions = get_role_permissions(user["role_id"])


def logout():
    global _current_user, _permissions
    _current_user = None
    _permissions = []


def current_user():
    return _current_user


def has_permission(view_key):
    if _current_user is None:
        return False
    return view_key in _permissions


def require(view_key):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            if not has_permission(view_key):
                return
            return fn(*args, **kwargs)
        return wrapper
    return decorator
