import { describe, it, expect } from 'vitest'
import { parseValues } from './api.js'

describe('parseValues', () => {
  it('accepts commas, spaces and newlines', () => {
    expect(parseValues('1, 2\n3 4')).toEqual([1, 2, 3, 4])
  })
  it('rejects non-numbers', () => {
    expect(() => parseValues('1, two')).toThrow()
  })
  it('rejects an empty box', () => {
    expect(() => parseValues('  ')).toThrow()
  })
})
