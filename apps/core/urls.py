from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("service-worker.js", views.service_worker, name="service-worker"),
    path("offline/", views.offline, name="offline"),
    path("assistente/", views.assistant, name="assistant"),
    path("privacidade/", views.privacy, name="privacy"),
    path("health/live/", views.health_live, name="health-live"),
    path("health/ready/", views.health_ready, name="health-ready"),
]
