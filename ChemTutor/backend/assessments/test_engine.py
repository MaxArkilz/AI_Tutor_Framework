"""Pure rubric tests also run without Django: python -m unittest assessments.test_engine."""
import copy
import json
from pathlib import Path
import unittest

from .engine import ExamValidationError, grade_attempt, public_question

BANK = json.loads((Path(__file__).parent / "data" / "prep_bank.json").read_text())
ATOMIC = [q for q in BANK["questions"] if q["topicId"] == "atomic"]


def correct_answers(questions):
    return {q["id"]: {"optionId": q["correctOptionId"]} for q in questions}


class GradingTests(unittest.TestCase):
    def test_bank_integrity(self):
        self.assertEqual(len({q["id"] for q in BANK["questions"]}), 24)
        for topic in BANK["topics"]:
            self.assertEqual(sum(q["topicId"] == topic["id"] for q in BANK["questions"]), 4)
        for question in BANK["questions"]:
            self.assertEqual(sum(o["id"] == question["correctOptionId"] for o in question["options"]), 1)

    def test_perfect_score(self):
        result = grade_attempt(ATOMIC, correct_answers(ATOMIC), BANK["topics"])
        self.assertEqual(result["overall"], {"earned": 4, "possible": 4, "percent": 100, "answered": 4, "total": 4})
        self.assertEqual(next(t for t in result["topics"] if t["id"] == "atomic")["status"], "strong")

    def test_incorrect_is_needs_work(self):
        answers = {q["id"]: {"optionId": q["options"][1]["id"]} for q in ATOMIC}
        topic = next(t for t in grade_attempt(ATOMIC, answers, BANK["topics"])["topics"] if t["id"] == "atomic")
        self.assertEqual(topic["percent"], 0)
        self.assertEqual(topic["status"], "needs-work")

    def test_skips_and_unassessed_topics_are_insufficient(self):
        result = grade_attempt(ATOMIC, {}, BANK["topics"])
        self.assertEqual(result["overall"]["percent"], 0)
        self.assertTrue(all(t["status"] == "insufficient-evidence" for t in result["topics"]))
        self.assertIsNone(next(t for t in result["topics"] if t["id"] == "acids")["percent"])

    def test_minimum_evidence_and_skip_denominator(self):
        for count, expected_score, expected_status in [(2, 50, "insufficient-evidence"), (3, 75, "developing")]:
            result = grade_attempt(ATOMIC, correct_answers(ATOMIC[:count]), BANK["topics"])
            topic = next(t for t in result["topics"] if t["id"] == "atomic")
            self.assertEqual(topic["percent"], expected_score)
            self.assertEqual(topic["status"], expected_status)

    def test_raw_boundaries(self):
        for weights, expected_status in [([30, 30, 20, 20], "strong"), ([20, 20, 20, 40], "developing"),
                                         ([300, 300, 196, 204], "developing"), ([200, 200, 196, 404], "needs-work")]:
            questions = copy.deepcopy(ATOMIC)
            for question, weight in zip(questions, weights):
                question["points"] = weight
            answers = correct_answers(questions)
            answers[questions[3]["id"]]["optionId"] = questions[3]["options"][1]["id"]
            topic = next(t for t in grade_attempt(questions, answers, BANK["topics"])["topics"] if t["id"] == "atomic")
            self.assertEqual(topic["status"], expected_status)

    def test_confidence_reasoning_and_misconception_evidence(self):
        answers = correct_answers(ATOMIC)
        answers[ATOMIC[0]["id"]] = {"optionId": ATOMIC[0]["options"][1]["id"], "confidence": 3, "reasoning": "My explanation"}
        result = grade_attempt(ATOMIC, answers, BANK["topics"])
        self.assertEqual(result["overall"]["percent"], 75)
        evidence = result["evidence"][0]
        self.assertEqual(evidence["confidence"], 3)
        self.assertEqual(evidence["reasoning"], "My explanation")
        self.assertEqual(evidence["possibleMisconceptionId"], "identity-is-neutrons")

    def test_invalid_answers_rejected(self):
        for answers in (None, [], {"unassigned": {}}, {ATOMIC[0]["id"]: []},
                        {ATOMIC[0]["id"]: {"optionId": "invalid"}},
                        {ATOMIC[0]["id"]: {"confidence": True}},
                        {ATOMIC[0]["id"]: {"confidence": 4}},
                        {ATOMIC[0]["id"]: {"reasoning": "x" * 2001}}):
            with self.subTest(answers=str(answers)[:60]), self.assertRaises(ExamValidationError):
                grade_attempt(ATOMIC, answers, BANK["topics"])

    def test_duplicate_assignments_rejected(self):
        with self.assertRaises(ExamValidationError):
            grade_attempt([ATOMIC[0], ATOMIC[0]], {}, BANK["topics"])

    def test_public_dto_hides_private_fields(self):
        for question in BANK["questions"]:
            dto = public_question(question)
            self.assertNotIn("correctOptionId", dto)
            self.assertNotIn("explanation", dto)
            for option in dto["options"]:
                self.assertEqual(set(option), {"id", "text"})
