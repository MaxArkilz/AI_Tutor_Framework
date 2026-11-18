/** Public API contracts. Answer keys exist only in submitted result evidence. */
export type TopicStatus = 'strong' | 'developing' | 'needs-work' | 'insufficient-evidence';
export interface ExamQuestion {
  id: string;
  version: number;
  type: 'single-choice';
  topicId: string;
  objectiveId: string;
  difficulty: number;
  points: number;
  prompt: string;
  options: { id: string; text: string }[];
}
export interface Answer {
  optionId?: string | null;
  confidence?: 1 | 2 | 3 | null;
  reasoning?: string;
}
export type AnswerMap = Record<string, Answer>;
export interface TopicResult {
  id: string;
  name: string;
  nextStep: string;
  assigned: number;
  answered: number;
  correct: number;
  earned: number;
  possible: number;
  ratio: number | null;
  percent: number | null;
  status: TopicStatus;
}
export interface ResponseEvidence {
  questionId: string;
  questionVersion: number;
  topicId: string;
  objectiveId: string;
  difficulty: number;
  prompt: string;
  optionId: string | null;
  selectedText: string | null;
  correct: boolean;
  pointsEarned: number;
  pointsPossible: number;
  confidence: 1 | 2 | 3 | null;
  reasoning: string;
  possibleMisconceptionId: string | null;
  correctAnswer: string;
  explanation: string;
}
export interface ExamResult {
  schemaVersion: number;
  rubricVersion: string;
  attemptId: string;
  bankVersion: string;
  startedAt: string;
  submittedAt: string;
  overall: { earned: number; possible: number; percent: number; answered: number; total: number };
  topics: TopicResult[];
  evidence: ResponseEvidence[];
}
export interface ExamAttempt {
  id: string;
  bankVersion: string;
  startedAt: string;
  topics: { id: string; name: string }[];
  questions: ExamQuestion[];
  result: ExamResult | null;
}
