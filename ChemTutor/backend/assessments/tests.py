"""Database/API integration tests, including session-CSRF and ownership checks."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.db import connection, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient, APITestCase

from .models import ExamAttempt, Question
from .services import create_attempt

BASE = "/api/assessments/"


class ExamAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_prep_exam", stdout=StringIO())
        cls.student = get_user_model().objects.create_user(username="student", password="test-password")
        cls.other = get_user_model().objects.create_user(username="other", password="test-password")

    def setUp(self):
        self.client.force_authenticate(self.student)

    def start(self):
        response = self.client.post(BASE + "attempts/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        return response.json()

    def submit(self, attempt_id, answers):
        return self.client.post(f"{BASE}attempts/{attempt_id}/submit/", {"answers": answers}, format="json")

    def test_balanced_unique_questions_and_hidden_keys(self):
        data = self.start()
        self.assertEqual(len(data["questions"]), 18)
        self.assertEqual(len({q["id"] for q in data["questions"]}), 18)
        self.assertEqual(set(Counter(q["topicId"] for q in data["questions"]).values()), {3})
        self.assertEqual(len(data["topics"]), 6)
        self.assertIsNone(data["result"])
        for q in data["questions"]:
            self.assertNotIn("correctOptionId", q)
            self.assertNotIn("explanation", q)
            self.assertTrue(all(set(o) == {"id", "text"} for o in q["options"]))
        saved = ExamAttempt.objects.get(pk=data["id"])
        self.assertEqual(saved.student, self.student)

    def test_anonymous_cannot_create_read_or_submit(self):
        attempt = self.start()
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(BASE + "attempts/", {}, format="json").status_code, 403)
        self.assertEqual(self.client.get(f"{BASE}attempts/{attempt['id']}/").status_code, 403)
        self.assertEqual(self.submit(attempt["id"], {}).status_code, 403)

    def test_other_student_cannot_read_or_submit(self):
        attempt = self.start()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"{BASE}attempts/{attempt['id']}/").status_code, 404)
        self.assertEqual(self.submit(attempt["id"], {}).status_code, 404)

    def test_submission_uses_snapshot_and_is_idempotent(self):
        attempt = self.start()
        saved = ExamAttempt.objects.get(pk=attempt["id"])
        answers = {q["id"]: {"optionId": q["correctOptionId"]} for q in saved.snapshot["questions"]}
        # Later authoring edits do not change this assigned exam.
        Question.objects.update(explanation="Edited after assignment")
        response = self.submit(attempt["id"], answers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["overall"]["percent"], 100)
        self.assertTrue(all(t["status"] == "strong" for t in result["topics"]))
        self.assertTrue(all(e["explanation"] != "Edited after assignment" for e in result["evidence"]))
        self.assertEqual(self.submit(attempt["id"], {}).json(), result)
        self.assertEqual(self.client.get(f"{BASE}attempts/{attempt['id']}/").json()["result"], result)
        saved.refresh_from_db()
        self.assertIsNotNone(saved.submitted_at)
        self.assertEqual(saved.answers, answers)

    def test_invalid_options_and_unassigned_ids_do_not_finalize(self):
        attempt = self.start()
        for answers in ({"fake": {}}, {attempt["questions"][0]["id"]: {"optionId": "fake"}}):
            self.assertEqual(self.submit(attempt["id"], answers).status_code, 400)
        self.assertIsNone(ExamAttempt.objects.get(pk=attempt["id"]).result)

    def test_authoring_option_ids_cannot_be_used_to_guess_the_key(self):
        attempt = self.start()
        question = attempt["questions"][0]
        bank_item = Question.objects.get(question_id=question["id"], version=question["version"])
        self.assertNotIn(bank_item.correct_option_id, [option["id"] for option in question["options"]])
        self.assertEqual(self.submit(attempt["id"], {question["id"]: {"optionId": bank_item.correct_option_id}}).status_code, 400)

    def test_forged_score_is_ignored(self):
        attempt = self.start()
        response = self.client.post(f"{BASE}attempts/{attempt['id']}/submit/",
                                    {"answers": {}, "score": 100, "student": self.other.pk}, format="json")
        self.assertEqual(response.json()["overall"]["percent"], 0)
        self.assertEqual(ExamAttempt.objects.get(pk=attempt["id"]).student, self.student)

    def test_pending_attempt_with_unknown_rubric_is_not_regraded(self):
        attempt = self.start()
        ExamAttempt.objects.filter(pk=attempt["id"]).update(rubric_version="unsupported-policy")
        self.assertEqual(self.submit(attempt["id"], {}).status_code, 409)
        self.assertIsNone(ExamAttempt.objects.get(pk=attempt["id"]).result)

    def test_session_mutations_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.student)
        self.assertEqual(client.post(BASE + "attempts/", {}, format="json").status_code, 403)
        session = client.get(BASE + "session/").json()
        self.assertTrue(session["authenticated"])
        self.assertIn("csrfToken", session)
        created = client.post(BASE + "attempts/", {}, format="json", HTTP_X_CSRFTOKEN=session["csrfToken"])
        self.assertEqual(created.status_code, 201)
        url = f"{BASE}attempts/{created.json()['id']}/submit/"
        self.assertEqual(client.post(url, {"answers": {}}, format="json").status_code, 403)
        self.assertEqual(client.post(url, {"answers": {}}, format="json", HTTP_X_CSRFTOKEN=session["csrfToken"]).status_code, 200)

    def test_bank_unavailable_does_not_make_partial_attempt(self):
        Question.objects.filter(topic_id="atomic").update(active=False)
        response = self.client.post(BASE + "attempts/", {}, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(ExamAttempt.objects.count(), 0)

    def test_only_latest_active_question_version_is_assigned(self):
        item = Question.objects.get(question_id="atomic-1")
        item.pk = None
        item.version = 2
        item.save()
        Question.objects.filter(question_id="atomic-4").update(active=False)
        attempt = create_attempt(self.student)
        matching = [q for q in attempt.snapshot["questions"] if q["id"] == "atomic-1"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["version"], 2)

    def test_seeding_is_idempotent_and_refuses_to_overwrite(self):
        call_command("seed_prep_exam", stdout=StringIO())
        self.assertEqual(Question.objects.count(), 24)
        Question.objects.filter(question_id="atomic-1").update(prompt="Instructor revision")
        with self.assertRaises(CommandError):
            call_command("seed_prep_exam", stdout=StringIO())

    def test_invalid_authoring_key_is_rejected(self):
        item = Question.objects.first()
        item.correct_option_id = "not-an-option"
        with self.assertRaises(ValidationError):
            item.full_clean()


@skipUnless(connection.vendor == "postgresql", "Concurrent row-lock behavior requires PostgreSQL")
class ConcurrentSubmissionTests(TransactionTestCase):
    def test_two_submissions_commit_one_immutable_result(self):
        call_command("seed_prep_exam", stdout=StringIO())
        user = get_user_model().objects.create_user(username="concurrent-student")
        attempt = create_attempt(user)
        answers = {q["id"]: {"optionId": q["correctOptionId"]} for q in attempt.snapshot["questions"]}
        barrier = Barrier(2)

        def submit(payload):
            client = APIClient()
            client.force_authenticate(user)
            try:
                barrier.wait(timeout=10)
                response = client.post(f"{BASE}attempts/{attempt.id}/submit/", {"answers": payload}, format="json")
                return response.status_code, response.json()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(submit, answers)
            second = pool.submit(submit, {})
            results = [first.result(timeout=20), second.result(timeout=20)]
        self.assertEqual([item[0] for item in results], [200, 200])
        self.assertEqual(results[0][1], results[1][1])
        self.assertIn(results[0][1]["overall"]["percent"], (0, 100))
        attempt.refresh_from_db()
        self.assertEqual(attempt.result, results[0][1])
