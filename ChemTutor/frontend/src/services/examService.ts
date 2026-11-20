import type { AnswerMap, ExamAttempt, ExamResult } from '../types/exam';

const BASE_URL = '/api/assessments';
interface ExamSession { authenticated: boolean; csrfToken: string; loginUrl: string }

export class ExamApiError extends Error {
  status: number;
  loginUrl?: string;

  constructor(message: string, status: number, loginUrl?: string) {
    super(message);
    this.name = 'ExamApiError';
    this.status = status;
    this.loginUrl = loginUrl;
  }
}

/** All calls use the same origin so Django session cookies and CSRF agree. */
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init, credentials: 'same-origin', cache: 'no-store',
      headers: { Accept: 'application/json', ...init.headers },
    });
  } catch {
    throw new ExamApiError('Could not reach the exam service. Your current answers are still on this page.', 0);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
      ? body.detail : 'The exam service could not complete this request. Please try again.';
    throw new ExamApiError(detail, response.status);
  }
  if (!body || typeof body !== 'object') throw new ExamApiError('The exam service returned an invalid response.', response.status);
  return body as T;
}

/** Refresh CSRF before mutations; do not retain tokens across logins. */
async function authenticatedSession(): Promise<ExamSession> {
  const session = await request<ExamSession>('/session/');
  if (!session.authenticated) throw new ExamApiError('Sign in before starting or submitting a saved exam.', 401, session.loginUrl);
  return session;
}

export const examService = {
  async createAttempt(): Promise<ExamAttempt> {
    const session = await authenticatedSession();
    return request<ExamAttempt>('/attempts/', {
      method: 'POST', headers: { 'X-CSRFToken': session.csrfToken },
    });
  },

  async submitAttempt(attemptId: string, answers: AnswerMap): Promise<ExamResult> {
    const session = await authenticatedSession();
    return request<ExamResult>(`/attempts/${encodeURIComponent(attemptId)}/submit/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': session.csrfToken },
      body: JSON.stringify({ answers }),
    });
  },

  async getAttempt(attemptId: string): Promise<ExamAttempt> {
    await authenticatedSession();
    return request<ExamAttempt>(`/attempts/${encodeURIComponent(attemptId)}/`);
  },
};
