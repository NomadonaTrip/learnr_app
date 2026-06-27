# User Experience Principles

### Visual Personality

**Design Tone:**
- **Professional & Trustworthy:** This is career-advancement, not casual learning
- **Clean & Focused:** Minimal distractions during study sessions
- **Encouraging & Supportive:** Motivational without being patronizing
- **Data-Driven & Transparent:** Show progress, competency, gaps clearly

**Color Psychology:**
- Primary: Professional blue (trust, competence, learning)
- Accents: Success green (correct answers, progress)
- Alerts: Warm orange (reviews due, attention needed - not alarming red)
- Neutrals: Clean grays and whites (text, backgrounds)

**Typography:**
- Clear, readable sans-serif for UI (e.g., Inter, Roboto)
- Larger font sizes for questions and explanations (readability priority)
- Adequate line spacing for sustained reading (BABOK content)

### Key Interactions

**Onboarding Flow:**
- **Pattern:** Progressive disclosure (one question at a time, not overwhelming)
- **Interaction:** Simple form inputs, clear progress indicator
- **Tone:** Friendly and conversational, sets expectations

**Diagnostic Assessment:**
- **Pattern:** Focused quiz mode (minimal chrome, just question and options)
- **Interaction:** Click/tap to select answer, clear "Submit" action
- **Feedback:** Immediate results after completion (not per-question during diagnostic)
- **Tone:** Neutral assessment (not judgmental, establishes baseline)

**Adaptive Quiz Sessions:**
- **Pattern:** Question → Answer → Explanation → Reading → Next
- **Interaction:**
  - Radio buttons or cards for answer selection
  - Clear visual feedback on correct/incorrect
  - Expandable/collapsible reading content (optional, not forced)
  - "Next Question" to continue
- **Tone:** Educational and supportive, celebrate successes, encourage on mistakes

**Progress Dashboard:**
- **Pattern:** Data visualization dashboard (hero section)
- **Interaction:**
  - At-a-glance competency bars (6 KAs)
  - Hover/tap for detailed stats
  - Click KA to see specific gaps and recommendations
  - Clear call-to-action: "Continue Learning" or "Start Review"
- **Tone:** Motivational and actionable (show progress, suggest next steps)

**Spaced Repetition Reviews:**
- **Pattern:** Clear labeling ("Review Mode" vs. "New Content")
- **Interaction:** Same quiz pattern, but with "Review" badge/icon
- **Visual:** Distinguish review questions (subtle color or icon difference)
- **Tone:** Reinforcement messaging ("Let's reinforce your understanding of...")

**Reading Content Display:**
- **Pattern:** Contextual content below explanation
- **Interaction:**
  - Auto-display after incorrect answer (helpful) or click "Learn More"
  - Readable formatting (proper spacing, highlighting key points)
  - "Mark as Read" or progress indicator
  - "Back to Quiz" or "Next Question" navigation
- **Tone:** Educational resource (this helps you learn, not just testing)

### Critical User Flows

**First-Time Learner Journey:**
1. Landing page with first onboarding question inline → Begin engagement immediately
2. Complete 7-question onboarding flow → Personalization established
3. Account creation prompt → Register with email/password
4. Initial diagnostic (12 questions) → Competency baseline set
5. Results & dashboard intro → Understand gaps and plan
6. First quiz session with reading → Experience full loop
7. Return to dashboard → See progress

**Daily Active Learner Journey:**
1. Log in → Dashboard shows progress and reviews due
2. Decision point: Reviews or new content
3. Quiz session (mixed or new)
4. See progress update
5. Log out or continue

**Pre-Exam Learner Journey:**
1. Dashboard shows "Exam ready" status (or gaps remaining)
2. Optional: Mock test (post-MVP)
3. Final reviews on weak areas
4. Confidence check
5. Take real exam

**First-Time Trainer Journey (NEW - v3.0):**
1. Trainer registers with trainer role (or is promoted by admin/organization admin)
2. Creates or joins an organization
3. Creates first class → Receives invite link/code for students
4. Students enroll via invite → Appear in class roster
5. Trainer views class dashboard → Sees initial diagnostic results as students complete them
6. Trainer configures at-risk alert thresholds (optional, sensible defaults provided)

**Daily Trainer Journey (NEW - v3.0):**
1. Log in → Organization dashboard shows KPI summary across all classes
2. Review at-risk alerts → Students flagged for low engagement or persistent gaps
3. Click into specific class → See concept mastery heatmap and class progress
4. Drill into individual student → See detailed belief states, quiz history, gap analysis
5. Optionally export progress report for stakeholder review
6. Plan classroom instruction based on class-wide weak concepts

**Trainer Intervention Journey (NEW - v3.0):**
1. Receive at-risk notification (in-app or email) for a student
2. Click through to student profile → See specific knowledge gaps
3. Review student's recent quiz sessions and reading engagement
4. Identify patterns (e.g., consistently wrong on prerequisite concepts)
5. Take action outside LearnR (classroom instruction, 1-on-1 support)
6. Monitor student progress over following days to validate intervention effectiveness

---
