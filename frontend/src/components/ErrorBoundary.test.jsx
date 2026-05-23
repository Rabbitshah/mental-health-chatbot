import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import ErrorBoundary from './ErrorBoundary'

// A component that throws on render
function BrokenComponent({ shouldThrow }) {
  if (shouldThrow) throw new Error('Test error')
  return <div>Working fine</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error noise from React's error boundary logging
  let consoleErrorSpy

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <BrokenComponent shouldThrow={false} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Working fine')).toBeInTheDocument()
  })

  it('displays fallback UI when a child component throws', () => {
    render(
      <ErrorBoundary>
        <BrokenComponent shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText(/unexpected error/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument()
  })

  it('logs the error to the console via componentDidCatch', () => {
    render(
      <ErrorBoundary>
        <BrokenComponent shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error caught by boundary:',
      expect.any(Error),
      expect.anything()
    )
  })
})
