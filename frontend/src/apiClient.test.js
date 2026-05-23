import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  ApiClient,
  getAccessToken,
  setAccessToken,
  getRefreshToken,
  setRefreshToken,
  clearTokens,
} from './apiClient'

// ── helpers ──────────────────────────────────────────────────────────────────

function makeResponse(status, body = {}) {
  const json = JSON.stringify(body)
  return new Response(json, {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

// ── token helper tests ────────────────────────────────────────────────────────

describe('token helpers', () => {
  beforeEach(() => clearTokens())

  it('stores and retrieves access token', () => {
    setAccessToken('abc')
    expect(getAccessToken()).toBe('abc')
  })

  it('stores and retrieves refresh token', () => {
    setRefreshToken('xyz')
    expect(getRefreshToken()).toBe('xyz')
  })

  it('clearTokens removes both tokens', () => {
    setAccessToken('a')
    setRefreshToken('b')
    clearTokens()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })
})

// ── ApiClient.request tests ───────────────────────────────────────────────────

describe('ApiClient.request', () => {
  let client
  let fetchSpy
  let consoleErrorSpy
  let consoleWarnSpy

  beforeEach(() => {
    clearTokens()
    client = new ApiClient()
    fetchSpy = vi.spyOn(globalThis, 'fetch')
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    fetchSpy.mockRestore()
    consoleErrorSpy.mockRestore()
    consoleWarnSpy.mockRestore()
    vi.useRealTimers()
  })

  it('returns response on 200', async () => {
    fetchSpy.mockResolvedValueOnce(makeResponse(200, { ok: true }))
    const res = await client.request('/test', { method: 'GET' }, { showErrorToast: false })
    expect(res.status).toBe(200)
  })

  it('attaches Authorization header when access token is set', async () => {
    setAccessToken('my-token')
    fetchSpy.mockResolvedValueOnce(makeResponse(200))
    await client.request('/test', {}, { showErrorToast: false })
    const [, opts] = fetchSpy.mock.calls[0]
    expect(opts.headers['Authorization']).toBe('Bearer my-token')
  })

  it('throws and logs on non-ok response', async () => {
    fetchSpy.mockResolvedValueOnce(makeResponse(400, { detail: 'Bad input' }))
    await expect(
      client.request('/test', {}, { showErrorToast: false })
    ).rejects.toThrow('Bad input')
    expect(consoleErrorSpy).toHaveBeenCalled()
  })

  it('retries on 500 with exponential backoff (up to MAX_RETRIES)', async () => {
    fetchSpy.mockResolvedValue(makeResponse(500, { detail: 'Server error' }))
    vi.useFakeTimers()

    let caughtError
    const promise = client
      .request('/test', {}, { showErrorToast: false })
      .catch((e) => { caughtError = e })

    await vi.runAllTimersAsync()
    await promise

    expect(caughtError).toBeDefined()
    // 1 initial + 3 retries = 4 calls
    expect(fetchSpy).toHaveBeenCalledTimes(4)
  })

  it('refreshes token on 401 and retries original request', async () => {
    setRefreshToken('refresh-tok')
    fetchSpy
      .mockResolvedValueOnce(makeResponse(401))
      .mockResolvedValueOnce(makeResponse(200, { access_token: 'new-access' }))
      .mockResolvedValueOnce(makeResponse(200, { data: 'ok' }))

    const res = await client.request('/protected', {}, { showErrorToast: false })
    expect(res.status).toBe(200)
    expect(getAccessToken()).toBe('new-access')
    expect(fetchSpy).toHaveBeenCalledTimes(3)
  })

  it('clears tokens and redirects to /login when refresh fails', async () => {
    setAccessToken('old')
    setRefreshToken('bad-refresh')
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    })

    fetchSpy
      .mockResolvedValueOnce(makeResponse(401))
      .mockResolvedValueOnce(makeResponse(401))

    await expect(
      client.request('/protected', {}, { showErrorToast: false })
    ).rejects.toThrow()

    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('logs network errors to console', async () => {
    vi.useFakeTimers()
    fetchSpy.mockRejectedValue(new Error('Network down'))

    let caughtError
    const promise = client
      .request('/test', {}, { showErrorToast: false })
      .catch((e) => { caughtError = e })

    await vi.runAllTimersAsync()
    await promise

    expect(caughtError).toBeDefined()
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      '[ApiClient] Network error',
      expect.objectContaining({ endpoint: '/test' })
    )
  })
})
