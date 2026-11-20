module.exports = {
  rootDir: '../..',
  testEnvironment: 'node',
  testMatch: ['<rootDir>/tests/prep-exam/**/*.test.cjs'],
  transform: { '^.+\\.tsx?$': '<rootDir>/tests/prep-exam/typescript-transform.cjs' },
};
