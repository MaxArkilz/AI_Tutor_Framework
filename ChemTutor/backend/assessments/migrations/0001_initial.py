import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Topic",
            fields=[("id", models.SlugField(max_length=64, primary_key=True, serialize=False)),
                    ("name", models.CharField(max_length=120)), ("next_step", models.TextField()),
                    ("active", models.BooleanField(default=True))],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="Question",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                    ("question_id", models.SlugField(max_length=64)), ("version", models.PositiveIntegerField(default=1)),
                    ("bank_version", models.CharField(max_length=64)), ("objective_id", models.SlugField(max_length=100)),
                    ("difficulty", models.PositiveSmallIntegerField(default=1)), ("prompt", models.TextField()),
                    ("options", models.JSONField()), ("correct_option_id", models.CharField(max_length=100)),
                    ("explanation", models.TextField()), ("points", models.PositiveSmallIntegerField(default=1)),
                    ("active", models.BooleanField(default=True)),
                    ("topic", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="questions", to="assessments.topic"))],
            options={"ordering": ["question_id", "-version"], "constraints": [
                models.UniqueConstraint(fields=("question_id", "version"), name="unique_question_version"),
                models.CheckConstraint(condition=models.Q(points__gte=1), name="question_positive_points"),
                models.CheckConstraint(condition=models.Q(version__gte=1), name="question_positive_version"),
            ]},
        ),
        migrations.CreateModel(
            name="ExamAttempt",
            fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                    ("bank_version", models.CharField(max_length=100)), ("rubric_version", models.CharField(max_length=64)),
                    ("snapshot", models.JSONField()), ("answers", models.JSONField(default=dict)),
                    ("result", models.JSONField(blank=True, null=True)), ("started_at", models.DateTimeField(auto_now_add=True)),
                    ("submitted_at", models.DateTimeField(blank=True, null=True)),
                    ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_attempts", to=settings.AUTH_USER_MODEL))],
            options={"ordering": ["-started_at"]},
        ),
    ]
