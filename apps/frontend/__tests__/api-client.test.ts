import { validateResponse } from '@/lib/api-client'
import { z } from 'zod'

jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  })),
}))

describe('api-client validateResponse', () => {
  it('returns parsed data when schema matches', () => {
    const schema = z.object({ id: z.number(), name: z.string() })
    const response = { data: { id: 1, name: 'Test' } }
    const result = validateResponse(response, schema)
    expect(result).toEqual({ id: 1, name: 'Test' })
  })

  it('returns raw data with warning when schema fails', () => {
    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation()
    const schema = z.object({ id: z.number() })
    const response = { data: { id: 'not-a-number' } }
    const result = validateResponse(response, schema)
    expect(result).toEqual({ id: 'not-a-number' })
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })
})
