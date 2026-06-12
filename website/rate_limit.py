from collections import defaultdict
from functools import wraps
from time import time

from flask import flash, render_template, request
from flask_login import current_user

_attempts = defaultdict(list)

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_WINDOW_SECONDS = 300


def is_rate_limited(endpoint, max_attempts=DEFAULT_MAX_ATTEMPTS, window_seconds=DEFAULT_WINDOW_SECONDS):
    key = f"{endpoint}:{request.remote_addr or 'unknown'}"
    now = time()
    recent = [t for t in _attempts[key] if now - t < window_seconds]
    _attempts[key] = recent
    return len(recent) >= max_attempts


def record_attempt(endpoint):
    key = f"{endpoint}:{request.remote_addr or 'unknown'}"
    _attempts[key].append(time())


def rate_limit_auth(template_name, max_attempts=DEFAULT_MAX_ATTEMPTS, window_seconds=DEFAULT_WINDOW_SECONDS):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if request.method == 'POST':
                if is_rate_limited(request.endpoint, max_attempts, window_seconds):
                    flash('Too many attempts. Please try again in a few minutes.', category='error')
                    return render_template(template_name, user=current_user)
                record_attempt(request.endpoint)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
