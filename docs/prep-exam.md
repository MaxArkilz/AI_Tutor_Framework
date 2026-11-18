# Chemistry preparation exam

The `/prep_exam` page runs an 18-question diagnostic using the Django question
bank. Questions are balanced across six topics, and question/option order is
randomized for every attempt. Completed attempts are saved to the signed-in
student; their result URL can be bookmarked and reopened after a refresh.
Answers still being edited are held only in React state and are lost on refresh
or navigation. The page explains this before starting.

## First use

From `ChemTutor/backend`, using your activated Python environment:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_prep_exam
python manage.py createsuperuser
python manage.py runserver
```

The existing PostgreSQL configuration remains the default. Set `DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, and optionally `DB_PORT` in the backend's
`.env`. For a separate, disposable local development database you may explicitly
set `DB_ENGINE=sqlite` instead. This does not copy PostgreSQL data into SQLite.

From `ChemTutor/frontend`, run the existing `npm ci` and `npm run dev` commands.
Vite proxies `/api/`, `/api-auth/`, `/byu/`, `/admin/`, and `/static/` to Django on
port 8000, so session cookies, login redirects, and CSRF use the frontend origin.
In production, route those paths to Django and serve the remaining paths through
the React app. An alternative deployment must account for cookie/CSRF origins.

Open `/prep_exam`, click Start exam, and follow Sign in if needed. With the
default `AUTH_TYPE=NONE`, the link uses Django REST Framework's session login.
The superuser created above is suitable for local testing. On a configured
institutional deployment, `AUTH_TYPE=OKTA` or `AUTH_TYPE=CAS` uses `/byu/login`.
SSO still requires the institution's actual credentials, allowed redirect URLs,
and a separate end-to-end login test; this change does not provision them.

## Authentication compatibility

The previous settings implicitly used Django's `auth.User`. That remains the
default, and all exam ownership uses `settings.AUTH_USER_MODEL`.
The existing `byu_auth.NewUser` is now swappable so it does not conflict with
the default model's permission relations. BYU user creation uses the configured
user model, and its admin registration is conditional.

A **fresh database** may opt into `AUTH_USER_MODEL=byu_auth.NewUser` before its
first migration. Do not change this setting on an existing populated database
without a planned user-data migration. No reset, data deletion, or user-table
conversion is performed by this feature.

The auth settings read their values from environment variables: `AUTH_TYPE`,
`FRONTEND_URL`, `FACULTY_GROUPS`, `ADMIN_GROUPS`, `INSPECTOR_GROUPS`,
`OKTA_CLIENT_ID`, `OKTA_CLIENT_SECRET`, `OKTA_DOMAIN`, `OKTA_LOGOUT_ENDPOINT`,
`TOKEN_ENDPOINT`, `CAS_CLIENT_ID`, `CAS_CLIENT_SECRET`, `CAS_REDIRECT_URI`,
`API_ID`, `API_SECRET`, `LOGIN_URL`, and `LOGOUT_ENDPOINT`.
Group lists and `CSRF_TRUSTED_ORIGINS` use comma-separated values. SSO routes
are loaded only when an SSO mode is enabled; CAS no longer initializes Okta.

## Structure

| File or area | Purpose |
| --- | --- |
| `frontend/src/pages/PrepExam.tsx` | Intro, questions, confidence/reasoning, review, results, saved-result loading |
| `frontend/src/types/exam.ts` | Typed public question, response, attempt, and result contracts |
| `frontend/src/services/examService.ts` | Session/CSRF-aware API calls and actionable errors |
| `frontend/src/CSSModules/prepExam.module.css` | Scoped exam styles |
| `backend/assessments/models.py` | Topics, versioned bank questions, and student-owned attempts |
| `backend/assessments/services.py` | Balanced selection, latest active versions, snapshots, public DTOs |
| `backend/assessments/engine.py` | Deterministic scoring and evidence generation |
| `backend/assessments/data/prep_bank.json` | The starter's 24 original example questions |
| `backend/assessments/admin.py` | Bank authoring and read-only attempt inspection |

The application does not ship answer keys in frontend assets. Public question
DTOs omit correct answers, explanations, and distractor tags. Assigned questions
use opaque option IDs unique to that attempt, so original option order cannot
identify the answer. Always submit option IDs from the returned question DTO.
Assigned questions
are snapshotted on the server so edits to the bank do not affect an existing
attempt. Only the attempt's owner can fetch or submit it. Answer review becomes
available after submission.

## Scoring

All seeded questions are worth one point. Overall and topic scores divide earned
points by assigned points; skipped questions earn zero. Authoring supports other
positive integer point values. Classifications use unrounded ratios:

| Condition | Topic signal |
| --- | --- |
| Fewer than 3 answered questions | Not enough evidence |
| At least 3 answered and score >=80% | Looking strong |
| At least 3 answered and score >=60%, <80% | Developing |
| At least 3 answered and score <60% | Needs practice |

With three one-point items, topic scores can only be 0%, 33%, 67%, or 100%.
These thresholds and the minimum of three are provisional product rules, not a
validated measure of mastery. Confidence and reasoning are optional and do not
change the score. A single tagged wrong answer is a possible misconception,
not a diagnosis. Retakes from this small bank are not independent evidence once
the student has reviewed the answers. Have instructors review the questions and
curriculum coverage before using results for placement.

## API

All endpoints are under `/api/assessments/`.

| Method/path | Response |
| --- | --- |
| `GET session/` | Authentication state, CSRF token, and login URL |
| `POST attempts/` | New assigned attempt, public questions, and topic names |
| `GET attempts/{uuid}/` | Owned attempt and its saved result, if submitted |
| `POST attempts/{uuid}/submit/` | Saved score, topic signals, explanations, and response evidence |

Create/read/submit require authentication. Mutations from session-authenticated
browsers require CSRF. The service obtains a fresh CSRF token before mutations,
including when the CSRF cookie itself is HTTP-only. Unauthenticated access gets
403 from Django REST Framework; the frontend also checks the public session
endpoint and displays a sign-in link before attempting mutations.

Submit body:

```json
{
  "answers": {
    "atomic-3": {
      "optionId": "an-opaque-option-id-from-this-attempt",
      "confidence": 2,
      "reasoning": "A positive ion has lost an electron."
    }
  }
}
```

Questions may be absent from the answer map to indicate a skip. `optionId` and
`confidence` may also be null. Confidence is 1, 2, or 3; reasoning is limited to
2,000 characters per question. Unknown question/option IDs and invalid evidence
metadata are rejected without finalizing the attempt. Client-supplied scores and
student IDs cannot control grading or ownership. Submission uses an atomic
transaction and a row lock on PostgreSQL; retries return the original result.

## Editing and seeding the bank

Use Django admin to maintain topics and questions. An option is an object with
an `id`, `text`, and optional `misconceptionId`. The correct-option field must
match exactly one unique option ID. Each question also identifies its topic,
learning objective, content version, explanation, points, and author-assigned
difficulty. Difficulty is metadata, not a calibrated test parameter.

Selection uses the latest active version of each question ID. Each active topic
must have at least three eligible questions; otherwise creation fails explicitly
instead of silently omitting the topic. To retire a topic, deactivate it. To
publish revised question content, create a higher version using the same stable
question ID. Historical attempts remain intact because they have snapshots.

`seed_prep_exam` can be run repeatedly. It creates missing rows but never
overwrites an existing question version. If seeded content was edited, it fails
and asks for a new version instead. Seeding does not reactivate retired items or
overwrite instructor edits to topics.

## Future local AI and personalization

Each saved result has schema/rubric/bank versions and per-question evidence:
question version, objective, selected answer, correctness, points, confidence,
reasoning, and a possible misconception ID. This is the input to a future
knowledge profile; a cumulative mastery model is not implemented here.

Add inference behind a backend adapter and enqueue it after a result is saved.
Send chemistry evidence rather than student identity. Validate structured
outputs and evidence references, and store model/prompt versions separately.
Suggested follow-up IDs should come from an eligible reviewed bank. Preserve the
original evidence and score when the model proposes an interpretation. Treat
student explanations as untrusted data in prompts and handle inference failures
without preventing exam completion. Earl's current simulated chat is unchanged.

## Tests

From `ChemTutor/backend`:

```bash
python manage.py test assessments --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
```

Test settings use an isolated SQLite database by default. The PostgreSQL CI job
explicitly sets `DB_ENGINE=postgresql` and supplies a disposable database; that
also runs a concurrent-submission test. Pure rubric tests run without Django:

```bash
python -m unittest assessments.test_engine -v
```

From the repository root, install the isolated frontend test tools and run Jest:

```bash
npm --prefix tests/prep-exam install
npm --prefix tests/prep-exam test
npm --prefix tests/prep-exam run typecheck
npm --prefix ChemTutor/frontend run build
```

The TypeScript check targets the new exam and its imports; it does not change
the existing application's TypeScript configuration. Test tools are isolated
from frontend production dependencies and its existing lockfile.

The Django suite covers selection, ownership, CSRF, snapshots, idempotency,
invalid/forged submissions, bank availability, seeding, and authoring validation.
Jest covers the TypeScript service's request bodies, cookies/CSRF, authentication,
and error handling. The pure suite covers exact scores, skips, evidence, and
classification boundaries. CI runs migration checks, database tests, Jest,
targeted TypeScript checking, and the Vite build.

Manual smoke check: sign in, start an exam, edit and clear answers, navigate
back/forward, submit with skips, inspect topic results and explanations, refresh
the saved-result URL, then confirm another account cannot open it. Check keyboard
navigation and the responsive topic table as well.
