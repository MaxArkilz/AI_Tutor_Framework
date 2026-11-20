import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTitle } from "../hooks/useTitle";
import { ExamApiError, examService } from "../services/examService";
import type { Answer, AnswerMap, ExamAttempt, ExamResult, TopicStatus } from "../types/exam";
import styles from "../CSSModules/prepExam.module.css";

type Phase = "intro" | "loading" | "exam" | "review" | "submitting" | "results";
interface Session { phase: Phase; attempt: ExamAttempt | null; result: ExamResult | null }

const STATUS_LABELS: Record<TopicStatus, string> = {
  strong: "Looking strong", developing: "Developing", "needs-work": "Needs practice",
  "insufficient-evidence": "Not enough evidence",
};

const CONFIDENCE_LABELS = [
  "Not set",
  "Guessing",
  "Somewhat sure",
  "Very sure",
] as const;

/** UI orchestrator. The service owns question selection and scoring. */
export default function PrepExam() {
  useTitle("Prep Exam | Chem Tutor");
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedAttemptId = searchParams.get("attempt");
  const [session, setSession] = useState<Session>({ phase: requestedAttemptId ? "loading" : "intro", attempt: null, result: null });
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [index, setIndex] = useState(0);
  const [error, setError] = useState("");
  const busy = useRef(false);
  const loadedAttemptId = useRef<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const [loginUrl, setLoginUrl] = useState<string | null>(null);
  const { phase, attempt, result } = session;
  const question = attempt?.questions[index];
  const answeredCount = attempt?.questions.filter(q => answers[q.id]?.optionId != null).length ?? 0;
  const confidence = question ? answers[question.id]?.confidence ?? null : null;
  const confidenceSliderValue = confidence ?? 0;

  useEffect(() => { heading.current?.focus(); }, [phase, index]);

  // Submitted exams have account-protected URLs that survive a refresh.
  useEffect(() => {
    if (!requestedAttemptId || loadedAttemptId.current === requestedAttemptId) return;
    let cancelled = false;
    busy.current = true;
    setError("");
    setLoginUrl(null);
    setSession({ phase: "loading", attempt: null, result: null });
    examService.getAttempt(requestedAttemptId).then(saved => {
      if (cancelled) return;
      if (!saved.result) throw new Error("This exam was not submitted. Start a new exam; draft answers are not saved.");
      loadedAttemptId.current = saved.id;
      setSession({ phase: "results", attempt: saved, result: saved.result });
    }).catch(err => {
      if (cancelled) return;
      if (err instanceof ExamApiError && err.loginUrl) setLoginUrl(err.loginUrl);
      setError(err instanceof Error ? err.message : "Could not load this saved exam.");
      setSession({ phase: "intro", attempt: null, result: null });
    }).finally(() => { if (!cancelled) busy.current = false; });
    return () => { cancelled = true; busy.current = false; };
  }, [requestedAttemptId]);

  async function startExam() {
    if (busy.current) return;
    busy.current = true;
    const previousSession = session;
    setError("");
    setLoginUrl(null);
    setSession((previous: Session) => ({ ...previous, phase: "loading" }));
    try {
      const nextAttempt = await examService.createAttempt();
      setAnswers({});
      setIndex(0);
      setSession({ phase: "exam", attempt: nextAttempt, result: null });
      loadedAttemptId.current = null;
      setSearchParams({}, { replace: true });
    } catch (err) {
      if (err instanceof ExamApiError && err.loginUrl) setLoginUrl(err.loginUrl);
      setError(err instanceof Error ? err.message : "Could not start the exam.");
      setSession(previousSession);
    } finally { busy.current = false; }
  }

  function updateAnswer(patch: Partial<Answer>) {
    if (!question) return;
    setAnswers((previous: AnswerMap) => ({
      ...previous,
      [question.id]: { ...previous[question.id], ...patch },
    }));
  }

  async function submitExam() {
    if (busy.current || !attempt) return;
    busy.current = true;
    setError("");
    setLoginUrl(null);
    setSession((previous: Session) => ({ ...previous, phase: "submitting" }));
    try {
      const nextResult = await examService.submitAttempt(attempt.id, answers);
      loadedAttemptId.current = nextResult.attemptId;
      setSession((previous: Session) => ({ ...previous, phase: "results", result: nextResult }));
      setSearchParams({ attempt: nextResult.attemptId }, { replace: true });
    } catch (err) {
      if (err instanceof ExamApiError && err.loginUrl) setLoginUrl(err.loginUrl);
      setError(err instanceof Error ? err.message : "Could not submit your answers. Try again.");
      setSession((previous: Session) => ({ ...previous, phase: "review" }));
    } finally { busy.current = false; }
  }

  return (
    <div className={styles["prep-exam"]}>
      <header>
        <p className={styles["prep-exam__eyebrow"]}>Chem Tutor / Find your starting point</p>
        <h1>Preparation exam</h1>
      </header>
      {error && <p className={styles["prep-exam__error"]} role="alert">{error} {loginUrl && <a href={loginUrl}>Sign in</a>}</p>}

      {phase === "intro" && <section className={styles["prep-exam__card"]}>
        <h2 ref={heading} tabIndex={-1}>What do you already know?</h2>
        <p>Answer three questions from each available introductory chemistry topic. There is no time limit.</p>
        <p>You can revisit or skip questions. Confidence and explanations are optional and do not affect your score.</p>
        <p>These results are a preliminary study guide. Sign in to save completed results to your account. Draft answers are saved only when you submit; refreshing or leaving clears your draft.</p>
        <button onClick={startExam}>Start exam</button>
      </section>}

      {phase === "loading" && <p role="status">Preparing your questions…</p>}

      {phase === "exam" && attempt && question && <section className={styles["prep-exam__card"]}>
        <div className={styles["prep-exam__row"]}>
          <span>Question {index + 1} of {attempt.questions.length}</span>
          <span>{attempt.topics.find(t => t.id === question.topicId)?.name}</span>
        </div>
        <label htmlFor="exam-progress">{answeredCount} of {attempt.questions.length} answered</label>
        <progress id="exam-progress" value={answeredCount} max={attempt.questions.length} />
        <h2 ref={heading} tabIndex={-1}>{question.prompt}</h2>
        <fieldset>
          <legend>Choose an answer</legend>
          {question.options.map(option => <label className={styles["prep-exam__option"]} key={option.id}>
            <input type="radio" name={question.id} value={option.id}
              checked={answers[question.id]?.optionId === option.id}
              onChange={() => updateAnswer({ optionId: option.id })} />
            <span>{option.text}</span>
          </label>)}
        </fieldset>
        <button className={styles["prep-exam__secondary"]} disabled={!answers[question.id]?.optionId}
          onClick={() => updateAnswer({ optionId: null })}>Clear answer</button>
        <div className={styles["prep-exam__optional"]} key={question.id}>
            <div className={styles["prep-exam__confidence-heading"]}>
              <label htmlFor="confidence">
                How confident are you? (optional)
              </label>
              <span
                className={styles["prep-exam__confidence-value"]}
                aria-live="polite"
              >
                {CONFIDENCE_LABELS[confidenceSliderValue]}
              </span>
            </div>
            <input
              id="confidence"
              className={styles["prep-exam__confidence-slider"]}
              type="range"
              min="0"
              max="3"
              step="1"
              value={confidenceSliderValue}
              aria-valuetext={CONFIDENCE_LABELS[confidenceSliderValue]}
              onChange={(e) => {
                const value = Number(e.currentTarget.value) as 0 | 1 | 2 | 3;
                updateAnswer({
                  confidence: value === 0 ? null : value,
                });
              }}
            />
            <div
              className={styles["prep-exam__confidence-labels"]}
              aria-hidden="true"
            >
              {CONFIDENCE_LABELS.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
          <label htmlFor="reasoning">Explain your thinking (optional)</label>
          <textarea id="reasoning" rows={3} maxLength={2000}
            value={answers[question.id]?.reasoning ?? ""}
            onChange={e => updateAnswer({ reasoning: e.target.value })} />
        </div>
        <nav className={styles["prep-exam__actions"]} aria-label="Question navigation">
          <button className={styles["prep-exam__secondary"]} disabled={index === 0}
            onClick={() => setIndex(i => i - 1)}>Previous</button>
          {index < attempt.questions.length - 1
            ? <button onClick={() => setIndex(i => i + 1)}>Next</button>
            : <button onClick={() => setSession((s: Session) => ({ ...s, phase: "review" }))}>Review answers</button>}
        </nav>
      </section>}

      {(phase === "review" || phase === "submitting") && attempt && <section className={styles["prep-exam__card"]}>
        <h2 ref={heading} tabIndex={-1}>Review before submitting</h2>
        <p>{answeredCount} of {attempt.questions.length} answered. Unanswered questions earn zero points.</p>
        <p>Each topic needs at least three answered questions for a preliminary topic rating.</p>
        <ol className={styles["prep-exam__review-list"]}>
          {attempt.questions.map((q, i) => <li key={q.id}>
            <button className={styles["prep-exam__secondary"]} disabled={phase === "submitting"}
              onClick={() => { setIndex(i); setSession((s: Session) => ({ ...s, phase: "exam" })); }}>
              Question {i + 1} — {answers[q.id]?.optionId ? "Answered" : "Unanswered"}
            </button>
          </li>)}
        </ol>
        <button onClick={submitExam} disabled={phase === "submitting"}>
          {phase === "submitting" ? "Scoring…" : "Submit exam"}
        </button>
      </section>}

      {phase === "results" && result && <>
        <section className={styles["prep-exam__card"]}>
          <h2 ref={heading} tabIndex={-1}>Your starting point</h2>
          <p className={styles["prep-exam__score"]}>{result.overall.percent}%</p>
          <p>{result.overall.earned} / {result.overall.possible} points · {result.overall.answered} / {result.overall.total} answered</p>
          <p>This result is saved to your account. Bookmark this page to return to it.</p>
          <p>Topic ratings are preliminary signals from a small sample, not confirmed mastery. Skipped questions count as zero in the score.</p>
          <div className={styles["prep-exam__table-wrap"]}><table>
            <caption>Performance by topic</caption>
            <thead><tr><th scope="col">Topic</th><th scope="col">Points</th><th scope="col">Answered</th><th scope="col">Current signal</th></tr></thead>
            <tbody>{result.topics.map(topic => <tr key={topic.id}>
              <th scope="row">{topic.name}</th>
              <td>{topic.assigned ? `${topic.earned}/${topic.possible} (${topic.percent}%)` : "Not assessed"}</td>
              <td>{topic.answered}/{topic.assigned}</td>
              <td><span className={`${styles["prep-exam__badge"]} ${styles[`prep-exam__badge--${topic.status}`]}`}>{STATUS_LABELS[topic.status]}</span></td>
            </tr>)}</tbody>
          </table></div>
          <h3>What to study next</h3>
          {result.topics.every(t => t.status === "strong")
            ? <p>Your sampled topics look strong. Try harder questions and explain your reasoning to check depth of understanding.</p>
            : <ul>{result.topics.filter(t => t.status !== "strong").map(topic => <li key={topic.id}>
              <strong>{topic.name}:</strong> {topic.status === "insufficient-evidence"
                ? "Answer more questions in this topic before drawing a conclusion." : topic.nextStep}
            </li>)}</ul>}
          <button onClick={startExam}>Try another exam</button>
        </section>
        <section className={styles["prep-exam__card"]}>
          <h2>Answer review</h2>
          <p>Reviewing these answers makes an immediate retake less useful for estimating your knowledge.</p>
          {result.evidence.map((item, i) => <details key={item.questionId}>
            <summary>Question {i + 1} — {item.correct ? "Correct" : item.optionId ? "Incorrect" : "Unanswered"}</summary>
            <p><strong>{item.prompt}</strong></p>
            <p>Your answer: {item.selectedText ?? "No answer"}</p>
            <p>Correct answer: {item.correctAnswer}</p>
            <p>{item.explanation}</p>
            {item.reasoning && <p>Your reasoning: {item.reasoning}</p>}
          </details>)}
        </section>
      </>}
    </div>
  );
}
