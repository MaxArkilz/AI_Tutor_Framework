const { examService, ExamApiError } = require('../../ChemTutor/frontend/src/services/examService.ts');

const originalFetch = global.fetch;
const session = { authenticated: true, csrfToken: 'csrf-test-token', loginUrl: '/api-auth/login/' };
const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });

beforeEach(() => { global.fetch = jest.fn(); });
afterEach(() => { global.fetch = originalFetch; });

test('create obtains fresh CSRF and posts with session credentials', async () => {
  const attempt = { id: 'attempt-id', questions: [], topics: [], result: null };
  fetch.mockResolvedValueOnce(response(session)).mockResolvedValueOnce(response(attempt, 201));
  await expect(examService.createAttempt()).resolves.toEqual(attempt);
  expect(fetch).toHaveBeenNthCalledWith(1, '/api/assessments/session/', expect.objectContaining({ credentials: 'same-origin' }));
  expect(fetch).toHaveBeenNthCalledWith(2, '/api/assessments/attempts/', expect.objectContaining({
    method: 'POST', credentials: 'same-origin', headers: expect.objectContaining({ 'X-CSRFToken': 'csrf-test-token' }),
  }));
});

test('submission sends answers and optional evidence, without client grading', async () => {
  const answers = { 'atomic-3': { optionId: 'atomic-3-0', confidence: 2, reasoning: 'It lost an electron.' } };
  const result = { overall: { percent: 100 } };
  fetch.mockResolvedValueOnce(response(session)).mockResolvedValueOnce(response(result));
  await expect(examService.submitAttempt('attempt-id', answers)).resolves.toEqual(result);
  expect(fetch.mock.calls[1][0]).toBe('/api/assessments/attempts/attempt-id/submit/');
  const options = fetch.mock.calls[1][1];
  expect(options.headers['X-CSRFToken']).toBe('csrf-test-token');
  expect(JSON.parse(options.body)).toEqual({ answers });
});

test('unauthenticated students receive a sign-in link without creating an attempt', async () => {
  fetch.mockResolvedValueOnce(response({ ...session, authenticated: false }));
  await expect(examService.createAttempt()).rejects.toMatchObject({ status: 401, loginUrl: '/api-auth/login/' });
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('expired login preserves the caller answer map and does not submit', async () => {
  const answers = { q: { optionId: 'answer' } };
  fetch.mockResolvedValueOnce(response({ ...session, authenticated: false }));
  await expect(examService.submitAttempt('attempt-id', answers)).rejects.toBeInstanceOf(ExamApiError);
  expect(answers).toEqual({ q: { optionId: 'answer' } });
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('server errors preserve useful details', async () => {
  fetch.mockResolvedValueOnce(response(session)).mockResolvedValueOnce(response({ detail: 'Bank needs more questions.' }, 503));
  await expect(examService.createAttempt()).rejects.toMatchObject({ message: 'Bank needs more questions.', status: 503 });
});

test('network failures are actionable', async () => {
  fetch.mockRejectedValueOnce(new TypeError('fetch failed'));
  await expect(examService.createAttempt()).rejects.toMatchObject({ status: 0, message: expect.stringContaining('Could not reach') });
});

test('non-JSON gateway errors do not leak a parser error', async () => {
  fetch.mockResolvedValueOnce({ ok: false, status: 502, json: async () => { throw new SyntaxError('HTML'); } });
  await expect(examService.createAttempt()).rejects.toMatchObject({ status: 502, message: expect.stringContaining('try again') });
});

test('saved attempt lookup encodes IDs and uses credentials', async () => {
  fetch.mockResolvedValueOnce(response(session)).mockResolvedValueOnce(response({ id: 'attempt-id', result: { overall: { percent: 67 } } }));
  const result = await examService.getAttempt('attempt /id');
  expect(result.result.overall.percent).toBe(67);
  expect(fetch).toHaveBeenCalledWith('/api/assessments/attempts/attempt%20%2Fid/', expect.objectContaining({ credentials: 'same-origin' }));
});

test('empty successful responses are rejected', async () => {
  fetch.mockResolvedValueOnce(response(session)).mockResolvedValueOnce(response(null));
  await expect(examService.getAttempt('attempt-id')).rejects.toMatchObject({ message: expect.stringContaining('invalid response') });
});
