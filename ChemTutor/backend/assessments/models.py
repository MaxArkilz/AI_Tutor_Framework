"""Question authoring and immutable, student-owned exam evidence."""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Topic(models.Model):
    id = models.SlugField(primary_key=True, max_length=64)
    name = models.CharField(max_length=120)
    next_step = models.TextField()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Question(models.Model):
    """A versioned bank item. Attempt snapshots preserve historical grading."""
    question_id = models.SlugField(max_length=64)
    version = models.PositiveIntegerField(default=1)
    bank_version = models.CharField(max_length=64)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="questions")
    objective_id = models.SlugField(max_length=100)
    difficulty = models.PositiveSmallIntegerField(default=1)
    prompt = models.TextField()
    options = models.JSONField()
    correct_option_id = models.CharField(max_length=100)
    explanation = models.TextField()
    points = models.PositiveSmallIntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["question_id", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["question_id", "version"], name="unique_question_version"),
            models.CheckConstraint(condition=models.Q(points__gte=1), name="question_positive_points"),
            models.CheckConstraint(condition=models.Q(version__gte=1), name="question_positive_version"),
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.options, list) or not 2 <= len(self.options) <= 8:
            raise ValidationError({"options": "Provide between two and eight options."})
        ids = []
        for option in self.options:
            if (not isinstance(option, dict) or not isinstance(option.get("id"), str)
                    or not option["id"] or not isinstance(option.get("text"), str)
                    or not option["text"].strip()
                    or ("misconceptionId" in option and not isinstance(option["misconceptionId"], str))):
                raise ValidationError({"options": "Each option needs a string id and nonempty text."})
            ids.append(option["id"])
        if len(set(ids)) != len(ids) or self.correct_option_id not in ids:
            raise ValidationError({"correct_option_id": "Options must have unique IDs and contain the answer key."})

    def __str__(self):
        return f"{self.question_id} v{self.version}"


class ExamAttempt(models.Model):
    """Private snapshots include keys; expose them only through public DTO helpers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_attempts")
    bank_version = models.CharField(max_length=100)
    rubric_version = models.CharField(max_length=64)
    snapshot = models.JSONField()
    answers = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
