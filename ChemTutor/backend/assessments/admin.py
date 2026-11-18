from django.contrib import admin
from .models import ExamAttempt, Question, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "active")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_id", "version", "topic", "objective_id", "difficulty", "active")
    list_filter = ("topic", "difficulty", "active")
    search_fields = ("question_id", "prompt", "objective_id")


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "started_at", "submitted_at")
    readonly_fields = ("id", "student", "bank_version", "rubric_version", "snapshot", "answers", "result", "started_at", "submitted_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
