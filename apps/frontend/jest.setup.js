require('@testing-library/jest-dom')

// Global mock for next/navigation (used by many components)
jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn(), back: jest.fn(), forward: jest.fn(), refresh: jest.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))
