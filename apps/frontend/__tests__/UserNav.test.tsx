import React from 'react'
import { render } from '@testing-library/react'
import { UserNav } from '@/components/user-nav'

jest.mock('@clerk/nextjs', () => ({
  UserButton: () => <div data-testid="user-button">UserButton</div>,
}))

describe('UserNav', () => {
  it('renders without crashing', () => {
    const { container } = render(<UserNav />)
    expect(container).toBeInTheDocument()
  })
})
