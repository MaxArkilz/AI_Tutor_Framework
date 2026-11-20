import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from assessments.models import Question, Topic


class Command(BaseCommand):
    help = "Load the demo bank without overwriting existing question versions."

    @transaction.atomic
    def handle(self, *args, **options):
        bank = json.loads((Path(__file__).resolve().parents[2] / "data" / "prep_bank.json").read_text())
        for topic in bank["topics"]:
            Topic.objects.get_or_create(id=topic["id"], defaults={"name": topic["name"], "next_step": topic["nextStep"]})
        created_count = 0
        for item in bank["questions"]:
            fields = {"bank_version": bank["bankVersion"], "topic_id": item["topicId"],
                      "objective_id": item["objectiveId"], "difficulty": item["difficulty"],
                      "prompt": item["prompt"], "options": item["options"],
                      "correct_option_id": item["correctOptionId"], "explanation": item["explanation"],
                      "points": item["points"]}
            question, created = Question.objects.get_or_create(question_id=item["id"], version=item["version"], defaults=fields)
            if not created and any(getattr(question, key) != value for key, value in fields.items()):
                raise CommandError(f"{question} differs from this bank. Publish a new version instead of overwriting it.")
            question.full_clean()
            created_count += created
        self.stdout.write(self.style.SUCCESS(f"Loaded {created_count} new questions; {len(bank['questions'])} demo items checked."))
