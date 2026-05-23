/**
 * Tests for lazy loading and code splitting (Requirement 17)
 */
import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { lazy, Suspense } from 'react'
import LoadingSpinner from './components/LoadingSpinner'

describe('Lazy loading with Suspense', () => {
  it('shows LoadingSpinner while a lazy component is loading', async () => {
    // Create a lazy component that never resolves during this test
    let resolveComponent
    const LazyComp = lazy(
      () =>
        new Promise((resolve) => {
          resolveComponent = () => resolve({ default: () => <div>Loaded!</div> })
        })
    )

    render(
      <Suspense fallback={<LoadingSpinner />}>
        <LazyComp />
      </Suspense>
    )

    // Spinner should be visible while component is loading
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeTruthy()
    // The lazy component content should NOT be visible yet
    expect(screen.queryByText('Loaded!')).not.toBeInTheDocument()

    // Resolve the lazy component
    resolveComponent()
    await waitFor(() => {
      expect(screen.getByText('Loaded!')).toBeInTheDocument()
    })
  })

  it('renders the component after lazy load completes', async () => {
    const LazyComp = lazy(() =>
      Promise.resolve({ default: () => <div data-testid="lazy-content">Lazy content</div> })
    )

    render(
      <Suspense fallback={<LoadingSpinner />}>
        <LazyComp />
      </Suspense>
    )

    await waitFor(() => {
      expect(screen.getByTestId('lazy-content')).toBeInTheDocument()
    })
  })

  it('LoadingSpinner renders without crashing', () => {
    render(<LoadingSpinner />)
    // Should render a spinner div
    const container = document.querySelector('.animate-spin')
    expect(container).toBeTruthy()
  })
})
