import hashlib

from django.core.cache import cache

from apps.core.services import client_ip

MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_SECONDS = 15 * 60


def login_attempt_key(request, email):
    identity = f"{client_ip(request) or 'unknown'}:{email.strip().lower()}"
    digest = hashlib.sha256(identity.encode()).hexdigest()
    return f"login-attempt:{digest}"


def login_is_blocked(request, email):
    return int(cache.get(login_attempt_key(request, email), 0)) >= MAX_LOGIN_ATTEMPTS


def record_failed_login(request, email):
    key = login_attempt_key(request, email)
    try:
        attempts = cache.incr(key)
    except ValueError:
        cache.set(key, 1, LOGIN_BLOCK_SECONDS)
        attempts = 1
    if attempts == 1:
        cache.touch(key, LOGIN_BLOCK_SECONDS)
    return attempts


def clear_login_attempts(request, email):
    cache.delete(login_attempt_key(request, email))
