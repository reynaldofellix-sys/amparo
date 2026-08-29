from functools import wraps

from django.http import JsonResponse


def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    "error": {
                        "code": "authentication_required",
                        "message": "Autenticação necessária.",
                    }
                },
                status=401,
            )
        return view(request, *args, **kwargs)

    return wrapped
