# Epic 3: Onboarding, Diagnostic & Initial Belief Seeding (BKT-First)

**Epic Goal:** Enable first-time users to complete onboarding, take an optimally-designed diagnostic assessment, and have their belief states initialized across the entire concept corpus. The diagnostic is not "12 random questions" but rather a carefully selected set of questions that maximizes initial information gain across the knowledge graph.

**Key Difference from Original:**
- Diagnostic questions are selected to maximize corpus coverage, not "3 per KA"
- Result is belief states for ALL concepts (500-1500), not 6 KA scores
- **User sees:** KA-level progress (6 bars) - unchanged from original UI
- **System knows:** Concept-level beliefs enabling smarter question selection

**Architecture Reference:** See `docs/architecture/bkt-architecture.md`

> **TODO (Multi-Course):** Epic references "CBAP" specifically but architecture supports multiple courses. Update epic language to be course-agnostic (e.g., "certification question" instead of "CBAP question"). Stories are being drafted with course-agnostic language.

---

## Story 3.1: Marketing Landing Page

*Redesigned as conversion-focused marketing page with premium Framer-inspired aesthetics*

As a **first-time visitor**,
I want to see a clear value proposition and benefits of the platform,
so that I understand how LearnR can help me achieve my learning goals and am motivated to start.

**Acceptance Criteria:**

### Navigation & Layout
1. Navigation bar is sticky with logo and "Get Started" CTA always visible
2. Hero section displays compelling headline, subtitle, and two CTAs ("Start exam prep", "I already have an account")
3. Benefits section showcases customer-focused outcomes (career change, certification success, etc.)
4. Features section explains how the platform delivers benefits (personalized learning, concept mastery, competence growth) in non-technical, welcoming language
5. Final CTA section (hero variant) appears before footer to convert scrollers
6. Footer contains standard links (About, Privacy, Terms, Contact)

### Navigation Behavior
7. "Start exam prep" CTA navigates to `/onboarding`
8. "I already have an account" navigates to `/login`

### Design System: Premium Framer-Inspired Aesthetics
9. **Typography Hierarchy:**
   - Primary font: Inter (system fallback: system-ui, sans-serif)
   - Hero headline: 56-88px (responsive scaling), font-weight 600
   - Section headers: 36-44px, font-weight 500
   - Body text: 16-18px, font-weight 400
   - Clear visual distinction between heading levels

10. **Glassmorphism Effects:**
    - Semi-transparent backgrounds with backdrop blur (blur-md to blur-xl)
    - Subtle borders with rgba white/black for depth
    - Layered cards with frosted glass appearance
    - Use sparingly on cards, modals, and floating elements

11. **Scroll Interactions:**
    - Parallax effects on hero background elements
    - Fade-in animations triggered on scroll into viewport
    - Staggered reveal for benefit/feature cards (sequential timing)
    - Smooth scroll behavior for internal anchor links

12. **Animation System:**
    - Spring-based animations (damping: 30, stiffness: 400)
    - Scale transitions from 0.95 → 1.0 on element appear
    - Hover states with subtle lift (translateY -2px) and shadow enhancement
    - Page load animations with staggered delays (50-100ms between elements)

13. **Color & Visual Polish:**
    - Warm cream/off-white backgrounds (#fffaf5 or similar)
    - Deep charcoal text (#121111) for high contrast readability
    - Primary blue accent (#3b82f6) for CTAs and interactive elements
    - Subtle gradient overlays for visual depth
    - Drop shadows: subtle, layered (multiple shadow values for realism)

14. **Spacing & Layout:**
    - Generous whitespace (80-160px between major sections)
    - Card border-radius: 14px (design system standard)
    - Consistent padding structure (64px sections, 24-40px internal)
    - Responsive grid: 1200px max-width, centered content

### Responsive & Accessibility
15. Mobile responsive (375px minimum width)
16. Accessibility: Keyboard navigable, screen reader friendly, WCAG AA compliant
17. Skip link to main content for screen readers
18. Color contrast meets 4.5:1 ratio for text

### Analytics
19. Track `landing_page_viewed` event on page load
20. Track `landing_cta_clicked` with `{ cta: 'start_exam_prep' | 'login' }`
21. Track scroll depth milestones (25%, 50%, 75%, 100%)

**Design References:**
- Scroll interactions: [Wallet Template](https://wallettemplate.framer.website/)
- Typography hierarchy: [Lunera Template](https://lunera.framer.ai/)
- Overall aesthetic: High-end Framer websites with glassmorphism, spring animations, and premium feel

---

## Story 3.2: Onboarding Questions (3 Questions)

*Redesigned: Course-agnostic 3-question flow for multi-course support*

As a **prospective user**,
I want to answer 3 quick onboarding questions about my learning goals,
so that the system can personalize my learning path.

**Acceptance Criteria:**
1. After clicking "Start exam prep" on landing page, navigate to `/onboarding`
2. Present questions 1-3 sequentially (one at a time, progress indicator)
3. Questions:
   - Q1: "I want to learn..." (course selection - currently only "Business Analysis")
   - Q2: "What's your 'why' for learning [course name]?" (Personal interest, Certification, Professional development, Career change, Other)
   - Q3: "How familiar are you with [course name]?" (New, Basics, Intermediate, Expert)
4. Q2 and Q3 dynamically display the selected course name from Q1
5. Responses stored in sessionStorage
6. Progress indicator: "Question X of 3"
7. Back button allows changing previous answers
8. All questions required (no skip option)
9. After Q3 → navigate to account creation
10. Q3 familiarity level maps to initial belief state priors for BKT:
    - New → 0.1, Basics → 0.3, Intermediate → 0.5, Expert → 0.7
11. Mobile responsive, accessible (consistent with Story 3.1 design system)
12. Analytics: Track completion rate, drop-off points

**Design Note:** This flow supports future multi-course expansion. Course-specific questions can be added dynamically based on Q1 selection.

---

## Story 3.3: Account Creation After Onboarding

*Largely unchanged, but adds belief state initialization trigger*

As a **engaged visitor**,
I want to create an account after completing onboarding,
so that my progress can be saved and I can access the diagnostic.

**Acceptance Criteria:**
1. After onboarding Q3 (familiarity), display account creation form
2. Fields: Email (required), Password (required), Name (optional)
3. Password requirements: 8+ chars, 1 uppercase, 1 number
4. Email validation (format check, uniqueness check via API)
5. Submit → POST `/api/v1/auth/register` with onboarding data
6. Backend creates user record with onboarding responses stored in profile
7. **Backend initializes belief states** for all concepts (Story 3.4 trigger)
8. Auto-login after registration (JWT token returned)
9. Redirect to `/diagnostic` after successful registration
10. Error handling: Email already exists, weak password, server errors
11. Social login option (Google OAuth) - stretch goal
12. Terms of Service and Privacy Policy links

**New for BKT:**
- AC7 triggers belief state initialization
- Initial belief prior derived from Q3 familiarity level (0.1, 0.3, 0.5, or 0.7)
- Onboarding data includes: course, motivation, familiarity, initialBeliefPrior

---

## Story 3.4: Belief State Initialization (NEW - CRITICAL)

As a **system**,
I want to initialize belief states for a new user across all concepts,
so that the BKT engine can track knowledge from the first question.

**Acceptance Criteria:**

1. Triggered automatically after user registration (Story 3.3)
2. Create `belief_states` records for ALL concepts in corpus using initialBeliefPrior from Q3:
   ```python
   # initialBeliefPrior from Q3: 0.1 (new), 0.3 (basics), 0.5 (intermediate), 0.7 (expert)
   prior = user.onboarding_data.initialBeliefPrior
   for concept in all_concepts:
       BeliefState.create(
           user_id=user.id,
           concept_id=concept.id,
           alpha=prior,      # From Q3 familiarity
           beta=1.0 - prior, # Complement
           response_count=0
       )
   ```
3. Bulk insert for performance (500-1500 records in single transaction)
4. Performance: Complete in <2 seconds
5. Idempotent: If belief states already exist, skip (handle retry scenarios)
6. Logging: "Initialized {N} belief states for user {id}"
7. Database indexes support efficient per-user queries
8. Error handling: Transaction rollback on failure, user notified
9. **No beliefs should have NULL values** - all concepts tracked from start
10. API endpoint: GET `/api/v1/beliefs/stats` returns initialization status

**Technical Notes:**
- Use bulk_insert_mappings for SQLAlchemy efficiency
- Consider background task if >2 seconds (but prefer synchronous for UX)

---

## Story 3.4.1: Familiarity-Based Belief Prior Integration (BUG FIX)

*Added to address implementation gap discovered during code review*

As a **system**,
I want to use the user's declared familiarity level from onboarding to set initial belief priors,
so that question selection is appropriately calibrated to the user's starting knowledge level.

**Background:**
Stories 3.3 and 3.4 specify that `initialBeliefPrior` from Q3 (New→0.1, Basics→0.3, Intermediate→0.5, Expert→0.7) should be used to initialize belief states. However, the implementation uses hardcoded `Beta(1,1)` for all users regardless of familiarity level. This story addresses that gap.

**Acceptance Criteria:**

1. **Backend Schema Update:**
   - Extend `UserCreate` schema to accept optional `onboarding_data` field:
     ```python
     class OnboardingData(BaseModel):
         course: str                    # 'business-analysis'
         motivation: str                # 'certification', etc.
         familiarity: str               # 'new', 'basics', 'intermediate', 'expert'
         initial_belief_prior: float    # 0.1, 0.3, 0.5, or 0.7

     class UserCreate(BaseModel):
         email: EmailStr
         password: str
         onboarding_data: OnboardingData | None = None
     ```

2. **Registration Route Update:**
   - Pass `course_id` (from `onboarding_data.course`) and `initial_belief_prior` to belief initialization service
   - Look up course by slug/name to get `course_id`

3. **Belief Initialization Service Update:**
   - Add `initial_belief_prior: float = 0.5` parameter to `initialize_beliefs_for_user()`
   - Calculate alpha/beta from prior:
     ```python
     # Use 10 pseudo-observations for reasonable initial confidence
     pseudo_observations = 10
     alpha = prior * pseudo_observations  # e.g., 0.3 * 10 = 3
     beta = (1 - prior) * pseudo_observations  # e.g., 0.7 * 10 = 7
     ```

4. **Database Function Update:**
   - Update `initialize_beliefs(p_user_id UUID)` to accept `p_alpha FLOAT, p_beta FLOAT` parameters
   - Or create new function `initialize_beliefs_with_prior(p_user_id UUID, p_alpha FLOAT, p_beta FLOAT)`

5. **Fallback Behavior:**
   - If `onboarding_data` is null (legacy users, API-only registration), use `Beta(1,1)` as default

6. **Testing:**
   - Unit test: Prior 0.1 → alpha=1, beta=9 (or scaled equivalent)
   - Unit test: Prior 0.7 → alpha=7, beta=3 (or scaled equivalent)
   - Integration test: Full registration flow with onboarding data sets correct priors
   - Integration test: Registration without onboarding data uses default `Beta(1,1)`

7. **Migration Consideration:**
   - Existing users with `Beta(1,1)` do not need migration (their beliefs have evolved through answers)

**Technical Notes:**
- The alpha/beta calculation uses `pseudo_observations` scaling to provide reasonable initial confidence
- Alternative: Use `alpha=prior, beta=1-prior` as specified in original epic (simpler but lower initial confidence)
- Recommend discussing scaling approach during story refinement

**Dependencies:**
- Story 3.3 (Account Creation) - frontend already sends onboarding_data
- Story 3.4 (Belief Initialization) - service to be modified

---

## Story 3.5: Optimal Diagnostic Question Selection (NEW - CRITICAL)

As a **system**,
I want to select diagnostic questions that maximize information gain across the concept corpus,
so that initial belief states are seeded efficiently.

**Acceptance Criteria:**

1. Diagnostic service selects 12-20 questions for initial assessment
2. Selection strategy: **Maximum Concept Coverage with Diversity**
   - Goal: Touch as many concepts as possible with minimal questions
   - Each question tests 1-5 concepts
   - Prefer questions that cover concepts not yet covered
   - Balance across knowledge areas (no more than 4 questions per KA)
   - Prefer questions with high discrimination (informative)
3. Algorithm:
   ```python
   def select_diagnostic_questions(concepts, questions, target_count=15):
       selected = []
       covered_concepts = set()
       ka_counts = defaultdict(int)

       # Score each question by uncovered concepts
       while len(selected) < target_count:
           best_question = max(
               available_questions,
               key=lambda q: (
                   len(set(q.concept_ids) - covered_concepts) * 10 +  # Coverage
                   q.discrimination * 5 +                              # Informativeness
                   (4 - ka_counts[q.ka]) * 2                          # KA balance
               )
           )
           selected.append(best_question)
           covered_concepts.update(best_question.concept_ids)
           ka_counts[best_question.ka] += 1

       return selected
   ```
4. Questions returned in randomized order (not clustered by concept)
5. API endpoint: GET `/api/v1/diagnostic/questions` returns selected questions
6. Response excludes correct_answer and explanation
7. Cache question selection per user (consistent if page refreshed)
8. Logging: "Selected {N} questions covering {M} concepts for diagnostic"
9. Performance: Selection completes in <500ms
10. Unit tests: Coverage optimization, KA balance, discrimination preference

**Target Coverage:**
- 15 questions should touch 40-60% of concepts
- Provides strong signal for high-level concept clusters
- Remaining concepts refined through adaptive quiz (Epic 4)

---

## Story 3.6: Diagnostic Assessment UI (REVISED)

As a **new user**,
I want to complete the diagnostic assessment in a focused interface,
so that my initial knowledge state can be measured.

**Acceptance Criteria:**

1. Navigate to `/diagnostic` after account creation
2. Fetch questions from GET `/api/v1/diagnostic/questions`
3. Display one question at a time (full-screen, minimal chrome)
4. Question display: Question text, 4 options (A/B/C/D as pill buttons)
5. Progress indicator: "Question X of {total}" + concept coverage meter
6. User selects option → "Submit Answer" button enabled
7. On submit: POST `/api/v1/diagnostic/answer` with question_id and selected_answer
8. **No immediate feedback** during diagnostic (different from quiz mode)
9. Auto-advance to next question after submission
10. 30-minute session timeout with warning at 25 minutes
11. No back button (can't change previous answers)
12. Browser navigation blocked with confirmation dialog
13. After last question → trigger belief update and redirect to results
14. Accessibility: Keyboard navigation, screen reader support
15. Mobile responsive (375px minimum)

**UI Additions for BKT:**
- Concept coverage meter (optional): Shows % of corpus touched
- "Building your knowledge profile..." messaging

---

## Story 3.7: Diagnostic Belief State Updates (NEW - CRITICAL)

As a **system**,
I want to update belief states after each diagnostic answer,
so that the user's knowledge profile is built incrementally.

**Acceptance Criteria:**

1. After each diagnostic answer, update beliefs for concepts tested by that question
2. Bayesian update using BKT formula:
   ```python
   def update_belief(belief, is_correct, slip=0.10, guess=0.25):
       p_mastered = belief.alpha / (belief.alpha + belief.beta)

       if is_correct:
           p_correct = (1 - slip) * p_mastered + guess * (1 - p_mastered)
           posterior = (1 - slip) * p_mastered / p_correct
       else:
           p_incorrect = slip * p_mastered + (1 - guess) * (1 - p_mastered)
           posterior = slip * p_mastered / p_incorrect

       belief.alpha += posterior
       belief.beta += (1 - posterior)
       belief.response_count += 1
       return belief
   ```
3. Update all concepts linked to the question (via question_concepts)
4. Persist updates after each answer (not batched)
5. Return updated belief summary in answer response:
   ```json
   {
     "is_recorded": true,
     "concepts_updated": ["uuid1", "uuid2"],
     "diagnostic_progress": 8,
     "diagnostic_total": 15
   }
   ```
6. Logging: "Updated beliefs for {N} concepts after question {id}"
7. Performance: Update completes in <100ms
8. Transaction: All belief updates atomic
9. Unit tests: Bayesian update math, multi-concept updates
10. Integration test: Full diagnostic updates all touched concepts

---

## Story 3.8: Diagnostic Results with Concept Coverage (REVISED)

As a **user who completed the diagnostic**,
I want to see my knowledge profile and areas needing focus,
so that I understand my starting point.

**Acceptance Criteria:**

1. Results screen displays after diagnostic completion
2. GET `/api/v1/diagnostic/results` returns:
   ```json
   {
     "total_concepts": 1203,
     "concepts_touched": 487,
     "coverage_percentage": 0.405,
     "estimated_mastered": 312,
     "estimated_gaps": 89,
     "uncertain": 802,
     "confidence_level": "initial",
     "by_knowledge_area": [
       {
         "ka": "Business Analysis Planning",
         "concepts": 187,
         "touched": 76,
         "estimated_mastery": 0.62
       }
       // ... 5 more KAs
     ],
     "top_gaps": [
       {"concept_id": "uuid", "name": "Stakeholder Analysis", "mastery_probability": 0.23}
       // ... top 10 gaps
     ],
     "recommendations": {
       "primary_focus": "Elicitation and Collaboration",
       "estimated_questions_to_coverage": 450,
       "message": "Great start! Your diagnostic touched 40% of CBAP concepts. Continue with adaptive quizzes to complete your knowledge profile."
     }
   }
   ```
3. **Hero Section:**
   - Coverage ring: "40% of concepts assessed"
   - Message: "Your knowledge profile is taking shape"
4. **Knowledge Area Breakdown:**
   - 6 horizontal bars showing per-KA coverage and estimated mastery
   - Color coding: Gray (not assessed), Red (<50%), Orange (50-70%), Green (>70%)
5. **Gap Highlights:**
   - Top 5-10 concepts identified as likely gaps
   - "Focus on these areas first" messaging
6. **Uncertainty Callout:**
   - "802 concepts still need assessment"
   - "Continue with adaptive quizzes to refine your profile"
7. **Primary CTA:** "Start Learning" → navigates to adaptive quiz
8. **Secondary CTA:** "Retake Diagnostic" (with confirmation)
9. Post-diagnostic survey: "How accurate does this feel?" (1-5)
10. Mobile responsive, accessible

**Key Messaging Change:**
- NOT "You scored 72%" (false precision)
- Instead: "We've started mapping your knowledge. Here's what we know so far."

---

## Story 3.9: Diagnostic Session Management (REVISED)

As a **system**,
I want to manage diagnostic session state,
so that users can resume interrupted diagnostics.

**Acceptance Criteria:**

1. `diagnostic_sessions` table:
   ```
   - id (UUID, PK)
   - user_id (FK)
   - question_ids (JSONB array) - selected questions for this diagnostic
   - current_index (INT) - progress through questions
   - status (ENUM: 'in_progress', 'completed', 'expired', 'reset')
   - started_at (TIMESTAMP)
   - completed_at (TIMESTAMP, nullable)
   - created_at
   ```
2. Session created when diagnostic questions fetched
3. Session updated after each answer (current_index++)
4. Session marked complete after last answer
5. Expired sessions (>30 min) marked as 'expired'
6. Only one active session per user
7. Resume support: If active session exists, return remaining questions
8. Reset endpoint: POST `/api/v1/diagnostic/reset` clears session and resets beliefs
9. Logging: Session state changes tracked
10. API returns session status for UI state management

---

## Removed Stories

The following stories from original Epic 3 are **removed or consolidated**:

- **Story 3.4 (Original): Question Selection by KA** → Replaced by Story 3.5 (Optimal Selection)
- **Story 3.6 (Original): Simplified IRT Calculation** → Replaced by Story 3.7 (BKT Updates)

---

## Dependencies

```
Epic 3 Dependencies:

3.1 (Landing) → 3.2 (Onboarding) → 3.3 (Account)
3.3 (Account) → 3.4 (Belief Init) → 3.4.1 (Prior Integration) → 3.5 (Question Selection)
3.5 → 3.6 (Diagnostic UI) → 3.7 (Belief Updates) → 3.8 (Results)
3.6 ↔ 3.9 (Session Management)

Note: Story 3.4.1 is a bug fix that can be implemented after 3.4 without blocking 3.5+.
      Existing users with Beta(1,1) beliefs will not be affected (their beliefs evolved through answers).

Requires from Epic 2:
- Concepts table populated (2.2)
- Questions with concept mappings (2.4)
- Belief state schema (from BKT architecture)
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Diagnostic completion rate | >80% |
| Average diagnostic time | 8-12 minutes |
| Concepts touched per diagnostic | 40-60% of corpus |
| Post-diagnostic survey "Accurate" | >70% |
| User proceeds to adaptive quiz | >75% |

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-12-20 | 2.3 | Added Story 3.4.1: Familiarity-Based Belief Prior Integration - addresses implementation gap where initialBeliefPrior from Q3 was not being used to set initial belief states (hardcoded Beta(1,1) instead of prior-based values) | John (Product Manager) |
| 2025-12-13 | 2.2 | Story 3.2: Redesigned to 3-question course-agnostic flow (course, motivation, familiarity) for multi-course support; Story 3.3: Updated Q6→Q3 reference; Story 3.4: Updated to use initialBeliefPrior from Q3 familiarity | Sarah (Product Owner) |
| 2025-12-13 | 2.1 | Story 3.1: Redesigned as marketing-only landing page (removed inline question); Added premium Framer-inspired design system (glassmorphism, spring animations, scroll interactions, typography hierarchy) | Sarah (Product Owner) |
| 2025-11-27 | 2.0 | Redesigned for BKT-first architecture; Added belief initialization (3.4); Replaced KA-based selection with optimal coverage (3.5); Replaced IRT scoring with Bayesian updates (3.7); Revised results for concept coverage (3.8) | Sarah (Product Owner) |
