import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { OnboardingPage } from '../../pages/OnboardingPage'

// Mock analytics service
vi.mock('../../services/analyticsService', () => ({
  trackOnboardingStarted: vi.fn(),
  trackOnboardingQuestionViewed: vi.fn(),
  trackOnboardingQuestionAnswered: vi.fn(),
  trackOnboardingCompleted: vi.fn(),
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderWithRouter = (initialRoute = '/onboarding') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <OnboardingPage />
    </MemoryRouter>
  )
}

describe('OnboardingPage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    mockNavigate.mockClear()
    vi.clearAllMocks()
  })

  describe('Initial Render', () => {
    it('renders progress indicator showing Q1', () => {
      renderWithRouter()
      expect(screen.getByText('Question 1 of 3')).toBeInTheDocument()
    })

    it('renders course selection question', () => {
      renderWithRouter()
      expect(screen.getByText('I want to learn...')).toBeInTheDocument()
    })

    it('renders Continue button', () => {
      renderWithRouter()
      expect(
        screen.getByRole('button', { name: /continue/i })
      ).toBeInTheDocument()
    })

    it('does not render Back button on Q1', () => {
      renderWithRouter()
      expect(
        screen.queryByRole('button', { name: /back/i })
      ).not.toBeInTheDocument()
    })

    it('Continue button is disabled initially', () => {
      renderWithRouter()
      expect(screen.getByRole('button', { name: /continue/i })).toBeDisabled()
    })
  })

  describe('Question Flow', () => {
    it('enables Continue button after selecting course', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      await user.click(screen.getByText('Business Analysis'))
      expect(screen.getByRole('button', { name: /continue/i })).toBeEnabled()
    })

    it('advances to Q2 after selecting course and clicking Continue', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      expect(screen.getByText('Question 2 of 3')).toBeInTheDocument()
      expect(
        screen.getByText("What's your 'why' for learning Business Analysis?")
      ).toBeInTheDocument()
    })

    it('shows Back button on Q2', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
    })

    it('advances to Q3 after Q2', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Q1
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q2
      await user.click(screen.getByText('Certification'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      expect(screen.getByText('Question 3 of 3')).toBeInTheDocument()
      expect(
        screen.getByText('How familiar are you with Business Analysis?')
      ).toBeInTheDocument()
    })

    it('navigates to /register after completing all questions', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Q1
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q2
      await user.click(screen.getByText('Certification'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q3
      await user.click(screen.getByText('I know the basics'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      expect(mockNavigate).toHaveBeenCalledWith('/register')
    })
  })

  describe('Back Button', () => {
    it('returns to Q1 from Q2', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Go to Q2
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Go back
      await user.click(screen.getByRole('button', { name: /back/i }))

      expect(screen.getByText('Question 1 of 3')).toBeInTheDocument()
      expect(screen.getByText('I want to learn...')).toBeInTheDocument()
    })

    it('preserves Q1 answer when going back from Q2', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Go to Q2
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Go back
      await user.click(screen.getByRole('button', { name: /back/i }))

      // Check that Business Analysis is still selected
      const button = screen.getByRole('button', { name: /business analysis/i })
      expect(button).toHaveAttribute('aria-pressed', 'true')
    })

    it('preserves Q2 answer when going back from Q3', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Q1
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q2
      await user.click(screen.getByText('Career change'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Go back to Q2
      await user.click(screen.getByRole('button', { name: /back/i }))

      // Check that Career change is still selected
      const button = screen.getByRole('button', { name: /career change/i })
      expect(button).toHaveAttribute('aria-pressed', 'true')
    })
  })

  describe('SessionStorage Persistence', () => {
    it('stores answers in sessionStorage', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      const stored = JSON.parse(sessionStorage.getItem('learnr_onboarding')!)
      expect(stored.course).toBe('business-analysis')
    })

    it('stores all answers after completion', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Q1
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q2
      await user.click(screen.getByText('Certification'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q3
      await user.click(screen.getByText('I know the basics'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      const stored = JSON.parse(sessionStorage.getItem('learnr_onboarding')!)
      expect(stored).toEqual({
        course: 'business-analysis',
        motivation: 'certification',
        familiarity: 'basics',
        initialBeliefPrior: 0.3,
      })
    })
  })

  describe('Resume Scenario', () => {
    it('resumes at Q2 when course is already answered', () => {
      sessionStorage.setItem(
        'learnr_onboarding',
        JSON.stringify({ course: 'business-analysis' })
      )

      renderWithRouter()
      expect(screen.getByText('Question 2 of 3')).toBeInTheDocument()
    })

    it('resumes at Q3 when course and motivation are answered', () => {
      sessionStorage.setItem(
        'learnr_onboarding',
        JSON.stringify({
          course: 'business-analysis',
          motivation: 'certification',
        })
      )

      renderWithRouter()
      expect(screen.getByText('Question 3 of 3')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has region role for question container', () => {
      renderWithRouter()
      expect(screen.getByRole('region')).toBeInTheDocument()
    })

    it('has aria-live polite for screen reader announcements', () => {
      renderWithRouter()
      const region = screen.getByRole('region')
      expect(region).toHaveAttribute('aria-live', 'polite')
    })

    it('has aria-label on question container', () => {
      renderWithRouter()
      const region = screen.getByRole('region')
      expect(region).toHaveAttribute('aria-label', 'Question 1 of 3')
    })
  })

  describe('BKT Prior Mapping', () => {
    it('sets initialBeliefPrior to 0.1 for new', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Q1
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q2
      await user.click(screen.getByText('Certification'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q3 - select "new"
      await user.click(screen.getByText("I'm new to Business Analysis"))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      const stored = JSON.parse(sessionStorage.getItem('learnr_onboarding')!)
      expect(stored.initialBeliefPrior).toBe(0.1)
    })

    it('sets initialBeliefPrior to 0.7 for expert', async () => {
      const user = userEvent.setup()
      renderWithRouter()

      // Q1
      await user.click(screen.getByText('Business Analysis'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q2
      await user.click(screen.getByText('Certification'))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      // Q3 - select "expert"
      await user.click(screen.getByText("I'm an expert brushing up my skills"))
      await user.click(screen.getByRole('button', { name: /continue/i }))

      const stored = JSON.parse(sessionStorage.getItem('learnr_onboarding')!)
      expect(stored.initialBeliefPrior).toBe(0.7)
    })
  })
})
