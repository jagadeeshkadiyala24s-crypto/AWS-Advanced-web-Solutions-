from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def role_required(role):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role != role:
                return HttpResponseForbidden('You do not have access to this page.')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
