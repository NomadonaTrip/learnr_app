# Product Scope

### MVP - Minimum Viable Product

**Core Learning Loop (MVP Scope):**

1. **Onboarding & Baseline Assessment**
   - 7-question onboarding flow (referral, exam type, motivation, date, knowledge level, target, commitment)
   - 12-question initial diagnostic (3 per knowledge area)
   - Immediate baseline competency results with gap analysis

3. **Adaptive Learning Engine**
   - Simplified Item Response Theory (IRT) competency estimation
   - Real-time competency tracking across 6 CBAP knowledge areas
   - Adaptive question selection (KA match + difficulty match + gap match)
   - 600-1,000 questions (500 gold standard vendor + LLM variations)

4. **Question Delivery & Feedback**
   - Adaptive quiz sessions (user-determined length)
   - Immediate answer feedback (correct/incorrect)
   - Detailed explanations for every question
   - Question metadata (KA, difficulty, concept tags)
   - **Zero-interruption flow** - reading materials added asynchronously to library

5. **Post-Session Review** (NEW - RETENTION BOOSTER)
   - Immediate re-presentation of all incorrect answers after session ends
   - User re-answers each question for reinforcement
   - Feedback: "Great improvement!" (incorrect → correct) or "Still incorrect"
   - Track reinforcement success rate (incorrect → correct)
   - Optional but highly encouraged (users can skip)
   - Summary shows improvement: "Original: 80% → Final: 93%"
   - **Expected Impact:** 2-3x better retention vs spaced repetition alone

6. **Asynchronous Reading Library** (NEW - CRITICAL DIFFERENTIATOR)
   - BABOK v3 content parsed and chunked (200-500 tokens per chunk)
   - Semantic search for relevant content based on user gaps + incorrect answers
   - Materials added to reading queue **asynchronously** (background process)
   - **Silent badge updates** - no popups, toasts, or interruptions
   - Dedicated Reading Library page with priority sorting (High/Medium/Low)
   - Filter by KA, priority, status (unread/reading/completed)
   - Rich context: shows which question prompted each recommendation
   - Engagement tracking: times opened, reading time, completion
   - Flexible actions: read now, mark complete, dismiss
   - **Key Benefit:** Zero interruption to learning flow; users read when ready

7. **Spaced Repetition System**
   - SM-2 algorithm adapted for 60-day exam timeline
   - Review intervals: 1 day → 3 days → 7 days → 14 days
   - Concept-level mastery tracking
   - Mixed sessions: 40% reviews + 60% new content (when reviews due)

8. **Progress Tracking & Visualization**
   - Dashboard with 6 KA competency bars
   - Weekly progress trends
   - Reviews due indicator
   - Exam readiness score
   - Target competency levels
   - **Reading Library** badge in navigation (unread count)

9. **User Account Management**
   - Email/password authentication
   - Profile and preferences storage
   - Session persistence across devices
   - Password reset capability

10. **Dark Mode Support** (NEW - ACCESSIBILITY & MODERN UX)
   - Light mode, dark mode, and auto (system preference) options
   - Complete dark mode color palette optimized for extended reading
   - Enhanced typography for dark backgrounds (larger font, increased line height)
   - Preference persists across devices (saved to user profile)
   - 200ms smooth transitions between modes
   - All components meet WCAG AA contrast requirements in both modes
   - **Key Benefit:** Reduces eye strain during extended study sessions, meets modern UX expectations

**MVP Exclusions (Explicitly Deferred):**
- Internal mock test (120-question full exam simulation)
- External mock test integration
- Time commitment validation logic (collect data only)
- Social/community features
- Mobile native apps (web-responsive only for MVP)
- Advanced analytics and insights
- Multiple certification support (CBAP only for MVP)

### Growth Features (Post-MVP)

**Phase 1 Extensions:**
- Internal mock test with full exam simulation
- Enhanced analytics (learning velocity, retention curves, prediction models)
- Time commitment tracking and validation
- Study streak tracking and gamification
- Content bookmarking and note-taking

**Phase 2 - Multi-Certification Expansion:**
- PSM1 (Professional Scrum Master) support
- CFA Level 1 support
- Generalized platform architecture for any certification
- Automated content pipeline for new certifications

**Phase 3 - Community & Social:**
- Study groups and peer learning
- Expert Q&A forums
- User-generated content (question submissions)
- Leaderboards and challenges

### Vision (Future)

**Enterprise & Institutional:**
- B2B offerings for corporate training
- Team dashboards and admin controls
- White-label solutions
- API access for partners

**Advanced Learning Features:**
- Personalized study plans with AI coaching
- Video explanations and multimedia content
- Live expert tutoring integration
- Weak area bootcamps (focused micro-courses)

**Platform Maturity:**
- Mobile native apps (iOS/Android via React Native)
- Offline mode support
- Multi-language support
- Advanced accessibility features

---
