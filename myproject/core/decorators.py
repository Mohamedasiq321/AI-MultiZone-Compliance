# decorators.py
from django.shortcuts import redirect
from functools import wraps

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            profile = getattr(request.user, "profile", None)
            if not profile or profile.role != role:
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
