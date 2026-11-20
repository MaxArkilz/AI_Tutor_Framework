from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import RUBRIC_VERSION, ExamValidationError, grade_attempt
from .models import ExamAttempt
from .services import BankUnavailable, attempt_dto, create_attempt


@method_decorator(never_cache, name="dispatch")
class SessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Obtain CSRF safely even when the CSRF cookie is HTTP-only."""
        login = "/byu/login" if settings.AUTH_TYPE in ("OKTA", "CAS") else reverse("rest_framework:login")
        return Response({"authenticated": request.user.is_authenticated,
                         "csrfToken": get_token(request),
                         "loginUrl": login + "?" + urlencode({"next": "/prep_exam"})})


class AttemptListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            attempt = create_attempt(request.user)
        except BankUnavailable as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(attempt_dto(attempt), status=status.HTTP_201_CREATED)


@method_decorator(never_cache, name="dispatch")
class AttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt, pk=attempt_id, student=request.user)
        return Response(attempt_dto(attempt))


class AttemptSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        # Row locking makes repeat/concurrent submission idempotent on PostgreSQL.
        with transaction.atomic():
            attempt = get_object_or_404(ExamAttempt.objects.select_for_update(), pk=attempt_id, student=request.user)
            if attempt.result is not None:
                return Response(attempt.result)
            if attempt.rubric_version != RUBRIC_VERSION:
                return Response({"detail": "This exam uses an unavailable scoring policy. Please start a new exam."},
                                status=status.HTTP_409_CONFLICT)
            try:
                answers = request.data.get("answers") if isinstance(request.data, dict) else None
                result = grade_attempt(attempt.snapshot["questions"], answers, attempt.snapshot["topics"])
            except ExamValidationError as error:
                return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
            attempt.submitted_at = timezone.now()
            result.update({"attemptId": str(attempt.id), "bankVersion": attempt.bank_version,
                           "startedAt": attempt.started_at.isoformat(),
                           "submittedAt": attempt.submitted_at.isoformat()})
            attempt.answers = answers
            attempt.result = result
            attempt.save(update_fields=["answers", "result", "submitted_at"])
        return Response(result)
