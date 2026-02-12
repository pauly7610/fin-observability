/**
 * Smoke tests — verify core components render without crashing.
 */
import React from 'react'
import { render, screen } from '@testing-library/react'

describe('Error Boundary', () => {
  it('renders error message and retry button', async () => {
    const { default: ErrorPage } = await import('../app/error')
    const mockReset = jest.fn()
    render(<ErrorPage error={new Error('Test failure')} reset={mockReset} />)
    expect(screen.getByText('Something went wrong')).toBeTruthy()
    expect(screen.getByText('Test failure')).toBeTruthy()
    expect(screen.getByText('Try again')).toBeTruthy()
  })

  it('calls reset when Try again is clicked', async () => {
    const { default: ErrorPage } = await import('../app/error')
    const mockReset = jest.fn()
    render(<ErrorPage error={new Error('Test failure')} reset={mockReset} />)
    screen.getByText('Try again').click()
    expect(mockReset).toHaveBeenCalledTimes(1)
  })
})
