from django.urls import path
from .views import AttemptDetailView, AttemptListView, AttemptSubmitView, SessionView

app_name = "assessments"
urlpatterns = [
    path("session/", SessionView.as_view(), name="session"),
    path("attempts/", AttemptListView.as_view(), name="attempt-list"),
    path("attempts/<uuid:attempt_id>/", AttemptDetailView.as_view(), name="attempt-detail"),
    path("attempts/<uuid:attempt_id>/submit/", AttemptSubmitView.as_view(), name="attempt-submit"),
]
