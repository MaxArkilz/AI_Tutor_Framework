"""Select balanced items and capture the authoritative versions for an attempt."""
import random
import uuid

from .engine import QUESTIONS_PER_TOPIC, RUBRIC_VERSION, public_question
from .models import ExamAttempt, Question, Topic


class BankUnavailable(ValueError):
    pass


def create_attempt(student):
    rng = random.SystemRandom()
    topics = list(Topic.objects.filter(active=True))
    if not topics:
        raise BankUnavailable("The question bank is not ready. Please ask your instructor to load it.")
    # Newest active version of each stable ID, never two versions of one item.
    versions = Question.objects.filter(active=True, topic__in=topics).order_by("question_id", "-version")
    latest = {}
    for item in versions:
        latest.setdefault(item.question_id, item)
    selected = []
    for topic in topics:
        candidates = [q for q in latest.values() if q.topic_id == topic.id]
        if len(candidates) < QUESTIONS_PER_TOPIC:
            raise BankUnavailable(f"The question bank needs at least {QUESTIONS_PER_TOPIC} active questions for {topic.name}.")
        selected.extend(rng.sample(candidates, QUESTIONS_PER_TOPIC))
    rng.shuffle(selected)
    questions = []
    for q in selected:
        q.full_clean()
        # Authoring IDs in the demo encode their original order. Use opaque,
        # attempt-specific IDs so shuffling cannot leak the correct choice.
        aliases = {option["id"]: uuid.uuid4().hex for option in q.options}
        options = [{**option, "sourceOptionId": option["id"], "id": aliases[option["id"]]} for option in q.options]
        rng.shuffle(options)
        questions.append({
            "id": q.question_id, "version": q.version, "type": "single-choice", "topicId": q.topic_id,
            "objectiveId": q.objective_id, "difficulty": q.difficulty, "points": q.points,
            "prompt": q.prompt, "options": options, "correctOptionId": aliases[q.correct_option_id],
            "explanation": q.explanation,
        })
    return ExamAttempt.objects.create(
        student=student, bank_version=",".join(sorted({q.bank_version for q in selected})),
        rubric_version=RUBRIC_VERSION,
        snapshot={"questions": questions, "topics": [
            {"id": t.id, "name": t.name, "nextStep": t.next_step} for t in topics
        ]},
    )


def attempt_dto(attempt):
    """Keys and distractor tags never leave the backend before submission."""
    return {
        "id": str(attempt.id), "bankVersion": attempt.bank_version,
        "startedAt": attempt.started_at.isoformat(),
        "topics": [{"id": t["id"], "name": t["name"]} for t in attempt.snapshot["topics"]],
        "questions": [public_question(q) for q in attempt.snapshot["questions"]],
        "result": attempt.result,
    }
