const nextJest = require('next/jest')

const createJestConfig = nextJest({ dir: './' })

/** @type {import('jest').Config} */
const customConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/app/(.*)$': '<rootDir>/app/$1',
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(@clerk)/)',
  ],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/', '<rootDir>/__tests__/test-utils.tsx', '<rootDir>/__tests__/mocks.ts'],
}

module.exports = createJestConfig(customConfig)
