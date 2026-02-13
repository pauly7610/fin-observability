import React from 'react'
import { render } from '@testing-library/react'
import { AuthTokenProvider } from '@/components/AuthTokenProvider'
import { setAuthTokenGetter } from '@/lib/api-client'

const mockSetAuthTokenGetter = jest.fn()
jest.mock('@/lib/api-client', () => ({
  setAuthTokenGetter: (fn: () => Promise<string | null>) => mockSetAuthTokenGetter(fn),
}))

const mockGetToken = jest.fn()
jest.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: mockGetToken }),
}))

describe('AuthTokenProvider', () => {
  beforeEach(() => {
    mockSetAuthTokenGetter.mockClear()
    mockGetToken.mockResolvedValue('test-token')
  })

  it('calls setAuthTokenGetter with getToken from useAuth', () => {
    render(
      <AuthTokenProvider>
        <span>Child</span>
      </AuthTokenProvider>
    )
    expect(mockSetAuthTokenGetter).toHaveBeenCalledWith(mockGetToken)
  })

  it('renders children', () => {
    const { getByText } = render(
      <AuthTokenProvider>
        <span>Child content</span>
      </AuthTokenProvider>
    )
    expect(getByText('Child content')).toBeInTheDocument()
  })
})
