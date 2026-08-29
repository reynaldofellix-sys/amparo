from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control

from .forms import AssistantForm
from .models import AssistantMessage
from .services import assistant_answer, audit


def landing(request):
    return render(request, "core/landing.html")


@cache_control(no_cache=True, must_revalidate=True)
def service_worker(request):
    response = render(request, "service-worker.js", content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "core/offline.html")


def health_live(request):
    return JsonResponse({"status": "ok", "service": "amparo"})


def health_ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable", "database": "error"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


@login_required
def assistant(request):
    form = AssistantForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        question = form.cleaned_data["question"]
        message = AssistantMessage.objects.create(
            user=request.user, question=question, answer=assistant_answer(question)
        )
        audit(
            event_type="assistant.question_asked", actor=request.user, request=request, obj=message
        )
        return redirect("assistant")
    messages = request.user.assistant_messages.all().order_by("-created_at")[:20]
    return render(
        request,
        "core/assistant.html",
        {"form": form, "assistant_messages": reversed(list(messages))},
    )


def privacy(request):
    recent_events = (
        request.user.auditevent_set.all()[:10] if request.user.is_authenticated else []
    )
    return render(request, "core/privacy.html", {"recent_events": recent_events})
