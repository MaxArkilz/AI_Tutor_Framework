"""Deterministic grading, independent of HTTP, database state, and future AI."""
RUBRIC_VERSION = "diagnostic-1"
MINIMUM_ANSWERED = 3
QUESTIONS_PER_TOPIC = 3


class ExamValidationError(ValueError):
    pass


def public_question(question):
    fields = ("id", "version", "type", "topicId", "objectiveId", "difficulty", "points", "prompt")
    return {**{key: question[key] for key in fields}, "options": [
        {"id": option["id"], "text": option["text"]} for option in question["options"]
    ]}


def grade_attempt(questions, answers, topics):
    """Skips earn zero; unanswered topics remain unknown. Confidence is ungraded."""
    if not questions or not isinstance(answers, dict):
        raise ExamValidationError("Invalid attempt or answers.")
    assigned = {q["id"] for q in questions}
    if len(assigned) != len(questions) or set(answers) - assigned:
        raise ExamValidationError("Answers must refer only to distinct assigned questions.")
    by_topic = {t["id"]: {**t, "assigned": 0, "answered": 0, "correct": 0,
                           "earned": 0, "possible": 0} for t in topics}
    evidence = []
    for q in questions:
        answer = answers.get(q["id"], {})
        if not isinstance(answer, dict):
            raise ExamValidationError("Invalid answer.")
        option_id = answer.get("optionId")
        selected = next((o for o in q["options"] if o["id"] == option_id), None)
        if option_id is not None and selected is None:
            raise ExamValidationError(f"Invalid option for {q['id']}.")
        confidence = answer.get("confidence")
        if confidence is not None and (type(confidence) is not int or confidence not in (1, 2, 3)):
            raise ExamValidationError("Confidence must be 1, 2, 3, or null.")
        reasoning = answer.get("reasoning", "")
        if not isinstance(reasoning, str) or len(reasoning) > 2000:
            raise ExamValidationError("Reasoning must contain at most 2000 characters.")
        correct = option_id == q["correctOptionId"]
        earned = q["points"] if correct else 0
        topic = by_topic[q["topicId"]]
        topic["assigned"] += 1
        topic["answered"] += selected is not None
        topic["correct"] += correct
        topic["earned"] += earned
        topic["possible"] += q["points"]
        evidence.append({
            "questionId": q["id"], "questionVersion": q["version"], "topicId": q["topicId"],
            "objectiveId": q["objectiveId"], "difficulty": q["difficulty"], "prompt": q["prompt"],
            "optionId": option_id, "selectedText": selected["text"] if selected else None,
            "correct": correct, "pointsEarned": earned, "pointsPossible": q["points"],
            "confidence": confidence, "reasoning": reasoning,
            "possibleMisconceptionId": selected.get("misconceptionId") if selected else None,
            "correctAnswer": next(o["text"] for o in q["options"] if o["id"] == q["correctOptionId"]),
            "explanation": q["explanation"],
        })
    topic_results = []
    for topic in by_topic.values():
        ratio = topic["earned"] / topic["possible"] if topic["possible"] else None
        if topic["answered"] < MINIMUM_ANSWERED:
            status = "insufficient-evidence"
        elif ratio >= .8:
            status = "strong"
        elif ratio < .6:
            status = "needs-work"
        else:
            status = "developing"
        # Match Math.round for nonnegative display values; classify before rounding.
        topic_results.append({**topic, "ratio": ratio,
                              "percent": int(ratio * 100 + .5) if ratio is not None else None,
                              "status": status})
    earned = sum(e["pointsEarned"] for e in evidence)
    possible = sum(e["pointsPossible"] for e in evidence)
    return {
        "schemaVersion": 1, "rubricVersion": RUBRIC_VERSION,
        "overall": {"earned": earned, "possible": possible, "percent": int(100 * earned / possible + .5),
                    "answered": sum(e["optionId"] is not None for e in evidence), "total": len(questions)},
        "topics": topic_results, "evidence": evidence,
    }
