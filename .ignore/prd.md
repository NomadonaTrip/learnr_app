# LearnR - Product Requirements Document

**Author:** Developer
**Date:** November 19, 2025
**Version:** 2.2

---

## Goals and Background Context

### Goals

The LearnR PRD aims to deliver the following desired outcomes:

- **Proven Learning Effectiveness**: Achieve 80%+ first-time pass rate for CBAP certification (vs. 60% industry average) through adaptive learning
- **Time Efficiency**: Reduce total study time by 30% (60-85 hours vs. 90-120 hours traditional methods) via intelligent content targeting
- **Complete Learning System**: Deliver integrated diagnostic → adaptive quiz → explanations → targeted reading → spaced repetition loop
- **Validated Differentiation**: Prove reading content feature provides measurable value (alpha test Day 24 validation)
- **Scalable Platform Foundation**: Establish architecture supporting multi-certification expansion (PSM1, CFA Level 1) within 6 months
- **User Confidence & Retention**: Maintain 80%+ daily engagement and 70%+ completion rates through exam day
- **Business Sustainability**: Create validated MVP ready for beta launch (Q1 2026) with clear path to profitability

### Background Context

Working professionals preparing for high-stakes certifications like CBAP face three compounding challenges: they don't know where to focus limited study time, existing tools (static quiz banks) don't adapt to individual gaps, and forgetting curves erode early learning without systematic review.

LearnR addresses this gap by combining AI-powered competency assessment, adaptive difficulty matching, immediate explanations, targeted BABOK v3 reading content, and spaced repetition into a complete learning system. Unlike competitors (Pocket Prep, Quizlet, expensive bootcamps), LearnR provides both testing AND teaching in one intelligent, personalized experience.

This PRD builds upon comprehensive project planning documented in the Project Brief (docs/brief.md) and 200+ strategic decisions (docs/note.md), including critical decisions to include reading content (Decision #23) and spaced repetition (Decision #31) in MVP scope. The platform targets career-advancing professionals (ages 30-45) who need efficient, self-paced preparation with transparent progress tracking.

Validation approach: 30-day MVP development → 30-day case study validation (exam Dec 21, 2025) → Go/No-Go decision (Day 24 alpha test validates reading content value) → Beta launch Q1 2026.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-17 | 1.0 | Initial PRD created with comprehensive functional and non-functional requirements | Developer |
| 2025-11-19 | 2.0 | Enhanced with Goals/Background, UI Design Goals, Technical Assumptions restructure, Epic List, User Stories with Acceptance Criteria, PM Checklist validation, and Next Steps prompts per B-MAD template | Developer |
| 2025-11-19 | 2.1 | **MAJOR UPDATE:** Added Post-Session Review feature for immediate reinforcement and Asynchronous Reading Library for zero-interruption learning flow. Approved design decisions #84-87. Complete technical specifications in Implementation_Summary.md | Developer |
| 2025-11-19 | 2.2 | Added MVP admin support tools: FR18 (Admin Operations and Support Tools), Story 8.7 (User Impersonation, User Search, PostHog Integration, Admin Audit Trail), PostHog analytics integration, admin-specific security requirements, admin_audit_log table, and users.is_admin column | Analyst Agent |

---

## Executive Summary

LearnR is an AI-powered adaptive learning platform that transforms professional certification exam preparation from passive memorization to active, adaptive mastery. The platform helps working professionals (ages 30-45) prepare for high-stakes certifications through intelligent competency assessment, personalized content delivery, and scientifically-proven retention techniques.

**Initial Market:** CBAP (Certified Business Analysis Professional) certification with expansion to PSM1, CFA Level 1, and additional professional certifications.

**Target Outcome:** 80%+ first-time pass rate (vs. 60% industry average) with 30% reduction in study time through adaptive content targeting.

### What Makes This Special

**Complete Adaptive Learning Loop:** Unlike static quiz banks, LearnR provides an intelligent, closed-loop learning system:

1. **Accurate Diagnostic** → Know exactly where you stand across all knowledge areas
2. **Adaptive Difficulty** → Study what you need, when you need it, at the right level
3. **Immediate Explanations** → Understand why answers are correct or incorrect
4. **Post-Session Review** (NEW) → Immediate reinforcement of incorrect answers for 2-3x better retention
5. **Asynchronous Reading Library** (NEW) → Curated BABOK content accessible on-demand without interrupting learning flow
6. **Spaced Repetition** → Scientific review scheduling for long-term retention
7. **Progress Transparency** → Real-time competency tracking with exam readiness indicators

**Key Innovation - "Test Fast, Read Later":** LearnR separates the momentum-driven testing experience from thoughtful reading study. Questions are answered in an uninterrupted flow, while reading materials accumulate asynchronously in a prioritized library. This dual-mode approach respects cognitive flow states and gives users complete control over when they engage with different learning activities.

This is not just a quiz app - it's a complete learning system that adapts to each user's knowledge gaps, reinforces learning immediately, and ensures retention through proven learning science.

---

## Project Classification

**Technical Type:** Web Application (SPA)
**Domain:** Educational Technology (EdTech) - Professional Certification
**Complexity:** Medium

**Technical Stack:**
- Frontend: React (web application, mobile-responsive)
- Backend: Python + FastAPI (RESTful API)
- SQL Database: PostgreSQL (user data, responses, tracking)
- Vector Database: Qdrant (questions + reading content, semantic search)
- AI/ML: OpenAI GPT-4 + Llama 3.1 (content generation), text-embedding-3-large (embeddings)
- Analytics: PostHog (product analytics, user behavior tracking, session replay)

**Domain Context:**
- Professional adult learners (30-45 years old)
- High-stakes certification exams (career advancement, salary impact)
- Limited study time (busy professionals with full-time jobs)
- Requires both assessment and learning capabilities
- Content must be accurate and validated (exam prep, not general education)

---

## Success Criteria

### User Success Metrics

**Primary Success Indicator:**
- **80%+ first-time pass rate** for CBAP certification (vs. industry average ~60%)

**Learning Efficiency:**
- **30% reduction in total study time** vs. traditional methods (through adaptive targeting)
- **90%+ users feel "exam-ready"** before taking the test (confidence metric)

**Engagement Indicators:**
- **80%+ daily active usage** during prep period (consistent engagement)
- **70%+ completion rate** (users who start complete their prep journey)
- **Spaced repetition reviews maintain 70%+ accuracy** (retention validation)
- **70%+ post-session review adoption rate** (NEW - users engage with review feature)
- **60%+ reinforcement success rate** (NEW - incorrect → correct on review)
- **50%+ reading completion rate** (NEW - vs 25% baseline with inline reading, +100% improvement)

**v2.1 Feature Validation (Async Reading Library):**
*Source: `docs/Asynchronous_Reading_Model.md` Lines 969-977 - Expected improvements from async model*

| Metric | Baseline (v2.0 Inline) | Target (v2.1 Async) | Improvement |
|--------|------------------------|---------------------|-------------|
| Reading engagement rate | 25% | 60%+ | +140% |
| Avg questions/session | 12 | 18+ | +50% |
| Session completion rate | 65% | 80%+ | +23% |
| Reading completion rate | 25% | 50%+ | +100% |

**Baseline Context:** v2.0 synchronous inline reading (deprecated) showed 25% engagement due to learning flow interruption. v2.1 asynchronous reading library targets 60%+ engagement through zero-interruption "test fast, read later" model.

### Product Validation Metrics

**MVP Validation (Case Study User - 60 Days):**
- User confirms diagnostic accuracy reflects actual knowledge level
- User reports reading content was relevant and helpful (80%+ helpful rating)
- User can articulate differentiation vs. competitor quiz apps
- User passes CBAP exam on first attempt (December 21, 2025)

**Go/No-Go Decision Criteria (Day 24 of MVP):**
- ✓ Complete learning loop functional (quiz → explanation → reading)
- ✓ User finds BABOK reading content valuable
- ✓ User commits to daily usage for remaining 30 days
- ✓ Differentiation from static quiz apps is clear

### Business Metrics

**Product-Market Fit:**
- Net Promoter Score (NPS) > 50
- Organic growth through word-of-mouth and testimonials
- 20%+ conversion rate (free trial to paid)

**Long-Term Viability:**
- Successfully launch 2nd certification within 6 months
- 90%+ retention through prep period
- Achieve business sustainability within 12 months

---

## Product Scope

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

## Educational Technology Specific Requirements

### Student Privacy & Data Protection

**Privacy Considerations:**
- User study data is personal and potentially sensitive (performance, gaps, struggles)
- Learning progress reveals user weaknesses (could impact confidence if exposed)
- Time spent and engagement patterns are behavioral data
- Exam results and certification goals are career-related information

**Data Handling Requirements:**
- Clear privacy policy explaining data usage
- User consent for data collection and AI processing
- No third-party data sharing without explicit consent
- Data retention policies (how long we keep performance data)
- User right to delete account and all associated data
- Secure storage of personally identifiable information (PII)

**Regulatory Compliance:**
- While COPPA/FERPA don't directly apply (adult learners, not K-12/university), follow privacy best practices
- Prepare for GDPR compliance (if expanding to EU users)
- Clear terms of service and user agreements

### Accessibility Requirements

**Target Accessibility Level: WCAG 2.1 Level AA**

**Critical Accessibility Features:**
- Keyboard navigation for all interactive elements
- Screen reader compatibility (semantic HTML, ARIA labels)
- Sufficient color contrast (4.5:1 for normal text, 3:1 for large text)
- Text resizing without loss of functionality (up to 200%)
- Focus indicators on interactive elements
- Alternative text for any images or diagrams
- Captions for any video/audio content (if added)

**Rationale:** Professional learners may have disabilities; ensuring accessibility broadens market and demonstrates quality.

### Content Quality & Moderation

**Content Accuracy Requirements:**
- Vendor questions validated by CBAP experts
- LLM-generated questions reviewed against gold standard
- Regular content quality audits
- User feedback mechanism for incorrect questions
- Content update process as BABOK evolves

**Explanation Quality:**
- All explanations reviewed for accuracy
- Clear, professional language (no ambiguity)
- References to BABOK sections when relevant
- User feedback on explanation helpfulness

**Reading Content Integrity:**
- BABOK content used appropriately (fair use for MVP, licensing for GA)
- Proper attribution and sourcing
- No modification of original BABOK meaning
- Chunk boundaries respect concept boundaries (don't break mid-concept)

---

## Web Application Specific Requirements

### Browser Support

**Supported Browsers (Latest 2 Versions):**
- Chrome/Chromium-based browsers (primary target)
- Firefox
- Safari (macOS and iOS)
- Edge

**Mobile Browser Support:**
- iOS Safari (iPhone/iPad)
- Chrome Mobile (Android)
- Responsive design for tablets and mobile devices

**Minimum Screen Resolutions:**
- Desktop: 1280x720 (minimum usable)
- Tablet: 768x1024 (iPad standard)
- Mobile: 375x667 (iPhone SE and up)

### Performance Targets

**Page Load Performance:**
- Initial page load < 3 seconds on 3G connection
- Time to interactive < 5 seconds
- Subsequent navigation < 1 second (SPA advantage)

**Quiz Experience Performance:**
- Question display < 500ms after answer submission
- Explanation and reading content load < 1 second
- Real-time competency updates (no visible delay)

### Progressive Web App (PWA) Considerations

**MVP PWA Features:**
- Service worker for offline error handling
- App manifest for "Add to Home Screen"
- Responsive and mobile-friendly design

**Future PWA Features (Post-MVP):**
- Full offline mode with local data sync
- Background sync for progress tracking
- Push notifications for review reminders

---

## User Experience Principles

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

**First-Time User Journey:**
1. Landing page with first onboarding question inline → Begin engagement immediately
2. Complete 7-question onboarding flow → Personalization established
3. Account creation prompt → Register with email/password
4. Initial diagnostic (12 questions) → Competency baseline set
5. Results & dashboard intro → Understand gaps and plan
6. First quiz session with reading → Experience full loop
7. Return to dashboard → See progress

**Daily Active User Journey:**
1. Log in → Dashboard shows progress and reviews due
2. Decision point: Reviews or new content
3. Quiz session (mixed or new)
4. See progress update
5. Log out or continue

**Pre-Exam User Journey:**
1. Dashboard shows "Exam ready" status (or gaps remaining)
2. Optional: Mock test (post-MVP)
3. Final reviews on weak areas
4. Confidence check
5. Take real exam

---

## User Interface Design Goals

This section captures the high-level UI/UX vision to guide design and development. The LearnR platform must deliver a professional, focused learning experience optimized for adult professionals preparing for career-advancing certifications.

### Overall UX Vision

LearnR's user experience should feel like **a personal learning coach** rather than a static testing tool. The platform continuously assesses, adapts, teaches, and motivates - creating a supportive environment that builds confidence while maintaining rigor. Every interaction should reinforce the value proposition: "This platform understands where I am, what I need to learn, and how to help me retain it."

**Key UX Principles:**
- **Trust through transparency**: Users always see their competency scores, gaps, and progress - no hiding weaknesses
- **Efficiency over entertainment**: Minimal distractions during study sessions; data visualizations are clear and actionable
- **Supportive, not patronizing**: Encouraging feedback without condescension; professional tone appropriate for career-focused adults
- **Personalized journey**: Every user's path is different based on their diagnostic results and ongoing performance

### Key Interaction Paradigms

**Progressive Disclosure (Onboarding)**
- One question at a time during onboarding flow (7 questions total)
- Clear progress indicators (Question 3 of 7)
- Friendly, conversational tone to set expectations and build rapport

**Focused Assessment Mode (Diagnostic & Quiz)**
- Minimal UI chrome during question answering - just question, options, and submit button
- Full-screen or centered focus to eliminate distractions
- Immediate visual feedback (correct = green, incorrect = orange/red) without interrupting flow
- Sequential flow: Question → Answer → Explanation → Reading → Next (guided progression)

**Data Dashboard (Progress Tracking)**
- At-a-glance competency visualization (6 KA bars with scores)
- Hero metrics prominent: Exam Readiness Score, Reviews Due, Days Until Exam
- Hover/tap interactions for drill-down details (KA-specific performance)
- Clear call-to-action: "Continue Learning" or "Start Reviews" based on state
- Weekly progress trends show improvement over time (motivational fuel)

**Contextual Content Presentation (Reading)**
- Reading content appears after explanations (logical learning sequence)
- Optional, not forced: Users can skip to next question or expand to read
- Readable formatting: Proper spacing, highlighted key points, BABOK section references
- Progress tracking: Mark as read, time spent, completion indicators

### Core Screens and Views

From a product perspective, these are the critical screens necessary to deliver the PRD values and goals:

1. **Landing Screen with Inline First Question** - Value proposition + first onboarding question (immediate engagement, no separate CTA)
2. **Onboarding Flow (Questions 2-7)** - Progressive disclosure, personalization questionnaire
3. **Account Creation Screen** - Prompted after question 7, email/password registration
4. **Diagnostic Assessment Screen** - 12-question baseline test (3 per KA), focused quiz mode
5. **Diagnostic Results Screen** - Competency breakdown by KA, gap analysis, recommendations
5. **Progress Dashboard (Home)** - 6 KA bars, exam readiness, reviews due, weekly trends, primary CTA
6. **Knowledge Area Detail View** - Drill-down per KA: competency, concept gaps, recent performance
7. **Quiz Session Screen** - Question display, answer selection, submission
8. **Explanation & Reading Screen** - Detailed explanations, targeted BABOK content, next question navigation
9. **Settings/Profile Screen** - Account management, preferences, exam date, privacy policy access

### Accessibility: WCAG 2.1 Level AA

LearnR commits to WCAG 2.1 Level AA compliance to ensure professional learners with disabilities can access the platform effectively and to demonstrate product quality.

**Critical Accessibility Features:**
- Keyboard navigation for all interactive elements (tab order, focus management)
- Screen reader compatibility (semantic HTML, ARIA labels, alt text for any images)
- Color contrast ratios: 4.5:1 for normal text, 3:1 for large text
- Text resizing up to 200% without loss of functionality
- Visible focus indicators on all interactive elements
- No flashing content (avoid seizure triggers)
- Descriptive labels and error messages

**Rationale:** Professional learners may have visual, motor, or cognitive disabilities. Accessibility broadens market reach and signals platform quality/professionalism.

### Branding

**Design Tone:**
- Professional & trustworthy (this is career advancement, not casual learning)
- Clean & focused (minimal distractions during study sessions)
- Encouraging & supportive (motivational without being patronizing)
- Data-driven & transparent (show progress, competency, gaps clearly)

**Color Psychology:**
- **Primary**: Professional blue (trust, competence, learning)
- **Success**: Green (correct answers, progress, achievement)
- **Attention**: Warm orange (reviews due, areas needing focus - not alarming red)
- **Neutrals**: Clean grays and whites (text, backgrounds, cards)

**Typography:**
- **Font Family:** Inter (primary typeface for all UI text)
- Larger font sizes for questions and explanations (readability priority)
- Adequate line spacing for sustained reading (BABOK content must be comfortable to read)
- Font weight hierarchy: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

**Visual Design System:**
- **Design Inspiration:** Framer website templates (modern, polished, professional aesthetic)
- **Icons:** Vector icons only - NO emojis used anywhere in the application
- **Card-based layouts** with hierarchical border radius system:
  - **Main screen containers:** 35px border radius (dashboard, quiz screens, major views)
  - **Primary information cards:** 22px border radius (competency cards, KA detail cards, explanation panels)
  - **Secondary cards:** 14px border radius (reading content chunks, stat cards, list items)
  - **Icon containers:** 8-12px border radius (avatar containers, small badges, icon buttons)
- **Buttons:** Pill-rounded shape (full border-radius: 9999px or 50%) for all CTAs and action buttons
- **Spacing & Layout:** Consistent padding and margins following 8px grid system
- **Elevation:** Subtle shadows for card depth, avoid heavy drop shadows

**Design System Tokens - Complete Specifications**

This section provides implementation-ready design tokens for all visual elements.

---

#### Color Palette (Light Mode)

| Color Token | Hex Code | Usage | Contrast |
|-------------|----------|-------|----------|
| `--color-primary` | `#0066CC` | Primary buttons, links, brand accents, progress bars | 4.5:1 on white |
| `--color-primary-dark` | `#004999` | Hover states, active buttons | 7:1 on white |
| `--color-primary-light` | `#E6F2FF` | Competency card backgrounds, subtle highlights | N/A |
| `--color-secondary` | `#6B7280` | Secondary text, metadata | 4.5:1 on white |
| `--color-success` | `#10B981` | Correct answers, high competency (>80%) | 4.5:1 on white |
| `--color-success-light` | `#D1FAE5` | Success backgrounds | N/A |
| `--color-warning` | `#F59E0B` | Reviews due, medium competency (60-80%) | 4.5:1 on white |
| `--color-warning-light` | `#FEF3C7` | Warning backgrounds | N/A |
| `--color-error` | `#EF4444` | Incorrect answers, low competency (<60%), high priority | 4.5:1 on white |
| `--color-error-light` | `#FEE2E2` | Error backgrounds | N/A |
| `--color-text-primary` | `#111827` | Headings, primary text | 12:1 on white |
| `--color-text-secondary` | `#374151` | Body text | 9:1 on white |
| `--color-text-tertiary` | `#6B7280` | Metadata, labels | 4.7:1 on white |
| `--color-border` | `#D1D5DB` | Dividers, card borders | N/A |
| `--color-bg-primary` | `#FFFFFF` | Page backgrounds | N/A |
| `--color-bg-secondary` | `#F9FAFB` | Card surfaces, subtle backgrounds | N/A |
| `--color-bg-tertiary` | `#F3F4F6` | Elevated cards | N/A |

**Color Psychology:**
- **Primary Blue (`#0066CC`)**: Trust, competence, learning (educational context)
- **Success Green (`#10B981`)**: Positive reinforcement, celebrates progress
- **Warning Orange (`#F59E0B`)**: Attention without panic (reviews due, not "failing")
- **Error Red (`#EF4444`)**: Clear feedback, paired with supportive messaging

---

#### Dark Mode Color Palette

**Activation:** Settings toggle - persists across devices via user profile

| Color Token | Dark Mode Value | Light Mode | Contrast |
|-------------|-----------------|------------|----------|
| `--bg-primary` | `#0F172A` (Slate 900) | `#FFFFFF` | N/A |
| `--bg-secondary` | `#1E293B` (Slate 800) | `#F9FAFB` | N/A |
| `--bg-tertiary` | `#334155` (Slate 700) | `#F3F4F6` | N/A |
| `--text-primary` | `#F1F5F9` (Slate 100) | `#111827` | 12:1 on Slate 900 |
| `--text-secondary` | `#CBD5E1` (Slate 300) | `#374151` | 8:1 on Slate 900 |
| `--text-tertiary` | `#94A3B8` (Slate 400) | `#6B7280` | 5:1 on Slate 900 |
| `--color-primary` | `#3B82F6` (Blue 500) | `#0066CC` | 4.5:1 on Slate 900 |
| `--color-primary-hover` | `#60A5FA` (Blue 400) | `#004999` | 6:1 on Slate 900 |
| `--color-success` | `#34D399` (Green 400) | `#10B981` | 4.5:1 on Slate 900 |
| `--color-warning` | `#FBBF24` (Amber 400) | `#F59E0B` | 4.5:1 on Slate 900 |
| `--color-error` | `#F87171` (Red 400) | `#EF4444` | 4.5:1 on Slate 900 |
| `--color-border` | `#475569` (Slate 600) | `#D1D5DB` | N/A |

**Implementation:**
- CSS custom properties updated via root class: `<html class="dark">`
- 200ms `ease-in-out` transition when toggling modes (prevents jarring flash)
- Tailwind dark mode variant: `dark:bg-slate-900`, `dark:text-slate-100`

---

#### Typography System

**Font Family:** Inter (Google Fonts)
- **Fallback:** system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Loading:** `font-display: swap` to prevent FOIT
- **Weights Used:** 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| `--text-h1` | 36px (2.25rem) | 700 | 1.2 (43px) | Page titles (rare) |
| `--text-h2` | 30px (1.875rem) | 700 | 1.3 (39px) | Section headers |
| `--text-h3` | 24px (1.5rem) | 600 | 1.4 (34px) | Subsection headers, KA names |
| `--text-h4` | 20px (1.25rem) | 600 | 1.5 (30px) | Component headers |
| `--text-body-lg` | 18px (1.125rem) | 400 | 1.6 (29px) | Question text, primary content |
| `--text-body` | 16px (1rem) | 400 | 1.5 (24px) | Default UI text, explanations |
| `--text-body-sm` | 14px (0.875rem) | 400 | 1.5 (21px) | Metadata, labels |
| `--text-caption` | 12px (0.75rem) | 500 | 1.4 (17px) | Badges, tags, timestamps |

**Typography Guidelines:**
- **Question Text:** 18-20px for readability during learning
- **Reading Content:** 16px with max-width 65-75 characters (optimal line length)
- **Mobile:** Scale down 10-15%, maintain line-height ratios
- **Paragraph Spacing:** 1.5-2em for multi-paragraph content

---

#### Spacing System

**Base Unit:** 4px (all spacing is multiple of 4)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px (0.25rem) | Tight spacing (icon + text) |
| `--space-sm` | 8px (0.5rem) | Component internal padding (badges, tags) |
| `--space-md` | 16px (1rem) | Default spacing (card padding, section gaps) |
| `--space-lg` | 24px (1.5rem) | Section spacing, generous card padding |
| `--space-xl` | 32px (2rem) | Major section breaks, dashboard sections |
| `--space-2xl` | 48px (3rem) | Page sections |
| `--space-3xl` | 64px (4rem) | Large breakouts |

**Layout Constraints:**
- **Touch Targets:** Minimum 48x48px on mobile (accessibility)
- **Container Max-Widths:**
  - Dashboard: 1280px
  - Quiz Session: 800px (focused, centered)
  - Reading Library: 1200px (3-column grid)
  - Reading Detail: 700px (optimal line length)

---

#### Border Radius Hierarchy

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-main` | 35px | Main screen containers (dashboard, quiz screens) |
| `--radius-primary` | 22px | Primary cards (competency cards, KA detail, explanations) |
| `--radius-secondary` | 14px | Secondary cards (reading chunks, stat cards, list items) |
| `--radius-icons` | 8-12px | Icon containers, small badges |
| `--radius-pill` | 9999px (full) | All buttons (pill-rounded CTAs) |

---

#### Icon System

**Library:** Heroicons (MIT License) - Outline style (24x24px) for most UI

**Core Icons:**
- Reading Library: Book icon (outline) + badge count
- Correct Answer: Check circle (solid, green)
- Incorrect Answer: X circle (solid, red)
- Master Level: Trophy/award icon
- Tooltip Info: Information circle (outline)
- Flag Question: Flag icon (outline)
- Navigation: Arrow icons (left/right)
- Settings: Cog icon
- Profile: User circle
- Dark Mode Toggle: Moon/Sun icons

**Icon Specifications:**
- **Sizes:** 20px (inline), 24px (standalone), 48px (hero)
- **Stroke Width:** 1.5-2px for outline icons
- **Color:** Inherit from parent or use theme colors
- **Accessibility:** Always paired with text label or ARIA label

---

#### CSS Custom Properties Structure

```css
:root {
  /* Colors - Light Mode */
  --color-primary: #0066CC;
  --color-primary-dark: #004999;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;

  --text-primary: #111827;
  --text-secondary: #374151;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F9FAFB;

  /* Typography */
  --font-family-primary: 'Inter', system-ui, sans-serif;
  --text-h1: 2.25rem;
  --text-body: 1rem;
  --line-height-body: 1.5;

  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;

  /* Border Radius */
  --radius-primary: 22px;
  --radius-secondary: 14px;
  --radius-pill: 9999px;
}

html.dark {
  /* Colors - Dark Mode Override */
  --color-primary: #3B82F6;
  --text-primary: #F1F5F9;
  --text-secondary: #CBD5E1;
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
}
```

**Development Rule:** NO hard-coded colors or spacing. All components must use design tokens via CSS custom properties.

### Dark Mode Typography Specifications (NEW MVP FEATURE)

Dark mode requires enhanced typography for optimal readability during extended study sessions:

**Light Mode Reading Typography:**
- Font size: 16px Inter
- Line height: 1.6 (26px)
- Color: `#374151` (Gray 700 - high contrast on white)

**Dark Mode Reading Typography (Enhanced):**
- Font size: **17px Inter** (1px larger for dark backgrounds)
- Line height: **1.7** (28.9px) - increased breathing room
- Color: `#CBD5E1` (Slate 300 - softer than pure white, reduces eye strain)
- Background: `#1E293B` (Slate 800 - not pure black, easier on eyes)

**Rationale:** Dark mode requires different typography settings for optimal readability. Larger font size and increased line height compensate for reduced contrast on dark backgrounds, reducing eye strain during extended reading sessions (critical for BABOK content consumption).

**Complete dark mode specs:** See `/docs/front-end-spec.md` Lines 2193-2227 (color palette), Lines 929-969 (reading view typography).

### Animation & Motion Design Specifications

LearnR uses subtle animations to enhance UX without overwhelming users. All animations respect cognitive flow and accessibility requirements.

**Animation Principles:**
- **Purposeful:** Every animation serves a functional purpose (feedback, guidance, or state transition)
- **Fast:** Animations complete in 200-400ms to feel responsive, not sluggish
- **Subtle:** No excessive bouncing, spinning, or attention-seeking effects (professional, not playful)
- **Accessible:** Respect `prefers-reduced-motion` media query - disable non-essential animations for users with vestibular disorders

**Key Animation Patterns:**

Complete animation specifications documented in `/docs/front-end-spec.md` Lines 2541-2643:

| Element | Animation | Timing | Purpose |
|---------|-----------|--------|---------|
| **Answer Feedback** | Pulse or shake | 200-300ms `ease-out` | Immediate visual confirmation of correct/incorrect |
| **Competency Bar Update** | Fill animation | 400ms `ease-in-out` | Show progress increase smoothly |
| **Reading Badge Pulse** | Scale 1.0 → 1.1 → 1.0 | 1000ms loop | Draw attention to new unread items (subtle) |
| **Perfect Session Celebration** | Confetti physics | 1500-2000ms | Reward achievement |
| **Dark Mode Toggle** | Color transition | 200ms `ease-in-out` | Prevent jarring flash when switching themes |
| **Modal Entry/Exit** | Fade + scale | 250ms `ease-out` | Smooth dialog transitions |
| **Question Transition** | Fade-in | 300ms | Smooth progression between questions |

**Accessibility Requirement:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Target Device and Platforms: Web Responsive

**Primary Target:** Web browsers (desktop and mobile)
- Desktop-optimized (1280x720 minimum, 1920x1080 ideal)
- Tablet-responsive (768x1024 iPad standard)
- Mobile-responsive (375x667 iPhone SE and up)

**Browser Support:**
- Chrome/Chromium-based browsers (primary target)
- Firefox, Safari, Edge (latest 2 versions)
- iOS Safari (iPhone/iPad), Chrome Mobile (Android)

**Post-MVP:** Native mobile apps (iOS & Android via React Native) planned for Phase 3 (Q2-Q3 2026) with offline mode and push notifications.

**Rationale:** Responsive web provides maximum reach with minimal development investment for MVP. Mobile-responsive design allows study anywhere. Native apps deferred until web platform validated.

---

## Functional Requirements

### FR1: Anonymous Onboarding & Personalization (Pre-Registration)

**FR1.1:** Landing page displays value proposition with first onboarding question inline (immediate engagement, no separate CTA button)
**FR1.2:** Users progress through 7 questions sequentially without authentication
**FR1.3:** System collects: (1) referral source, (2) certification choice, (3) motivation, (4) exam date, (5) current knowledge level, (6) target score, (7) daily study time
**FR1.4:** System stores onboarding responses temporarily in browser session/localStorage (no server storage yet)
**FR1.5:** After question 7, system prompts: "Create your account to save your progress and start your diagnostic assessment"
**FR1.6:** System persists all 7 onboarding answers to user profile upon account creation
**FR1.7:** Users can update onboarding preferences anytime from settings after registration

### FR2: User Account & Authentication (Post-Onboarding)

**FR2.1:** Users create accounts with email and password after completing 7-question onboarding flow
**FR2.2:** Account creation form pre-fills with onboarding context (e.g., exam date already collected)
**FR2.3:** Users can log in securely with email and password on return visits
**FR2.4:** Users can reset forgotten passwords via email verification
**FR2.5:** Users can update email address and password from settings
**FR2.6:** Users can delete their account and all associated data
**FR2.7:** System maintains user sessions across browser sessions (7-day JWT expiration)
**FR2.8:** System logs users out after 7 days of inactivity for security

### FR3: Personalization & Preference Management

**FR3.1:** System uses exam date to calculate days remaining (displayed on dashboard)
**FR3.2:** System uses knowledge level and target score to set initial recommendations
**FR3.3:** System stores all onboarding preferences in user profile for adaptive algorithm
**FR3.4:** Users can update preferences anytime from settings (exam date, target score, daily study time)
**FR3.5:** Preference changes immediately affect recommendations and pacing suggestions

### FR4: Initial Diagnostic Assessment

**FR4.1:** Users take a 12-question diagnostic assessment immediately after account creation (3 questions per KA, 6 KAs total)
**FR4.2:** System presents diagnostic questions in balanced order (not clustered by KA)
**FR4.3:** System provides no feedback during diagnostic (answers only recorded)
**FR4.4:** System calculates baseline competency scores for all 6 KAs after completion
**FR4.5:** System presents diagnostic results with competency bars and gap analysis
**FR4.6:** System recommends which KAs to focus on based on diagnostic results
**FR4.7:** Users can retake diagnostic at any time from settings (resets competency baseline)

### FR5: Competency Tracking & Estimation

**FR5.1:** System maintains real-time competency scores for each of 6 CBAP knowledge areas
**FR5.2:** System updates competency scores after every quiz response using IRT model
**FR5.3:** System calculates exam readiness score based on all 6 KA competencies
**FR5.4:** System tracks user performance history (all responses, timestamps, questions)
**FR5.5:** System calculates weekly progress deltas (improvement tracking)
**FR5.6:** System identifies specific concept gaps within each KA
**FR5.7:** System provides competency predictions (projected readiness by exam date)

### FR5A: Adaptive Question Selection

**FR5A.1:** System selects questions adaptively based on user competency profile
**FR5A.2:** System prioritizes questions from weakest knowledge areas
**FR5A.3:** System matches question difficulty to user's current competency level (+/- 1 level)
**FR5A.4:** System prevents recently seen questions from reappearing (minimum 7 days between repeats)
**FR5A.5:** System mixes question sources (gold standard + LLM variations) transparently
**FR5A.6:** System tracks which questions user has seen and answered
**FR5A.7:** System adjusts difficulty up after consecutive correct answers (3+)
**FR5A.8:** System adjusts difficulty down after consecutive incorrect answers (3+)

### FR6: Quiz Session Management

**FR6.1:** Users can start a quiz session from dashboard
**FR6.2:** System creates a mixed session (reviews + new content) when reviews are due
**FR6.3:** System creates a new content session when no reviews are due
**FR6.4:** Users answer questions one at a time (single question focus)
**FR6.5:** Users can pause/exit quiz session anytime (progress saved)
**FR6.6:** Users can resume paused sessions from where they left off
**FR6.7:** System tracks session metadata (start time, duration, questions answered)
**FR6.8:** Users can end session early or continue indefinitely (user-controlled length)

### FR7: Question Presentation & Answer Submission

**FR7.1:** System displays question text with 4 multiple-choice options (A, B, C, D)
**FR7.2:** System displays question metadata: Knowledge Area, Progress indicator (X of Y in session)
**FR7.3:** Users select one answer option (radio button or card selection)
**FR7.4:** Users submit answer with clear "Submit Answer" action
**FR7.5:** System provides immediate visual feedback (correct = green, incorrect = red/orange)
**FR7.6:** System prevents answer changes after submission (committed answer)
**FR7.7:** System records response, timestamp, time taken, and correctness

### FR8: Answer Explanations

**FR8.1:** System displays detailed explanation immediately after answer submission
**FR8.2:** Explanation includes: why correct answer is correct, why incorrect options are wrong
**FR8.3:** Explanation references BABOK section when applicable
**FR8.4:** Users can rate explanation helpfulness (thumbs up/down)
**FR8.5:** Users can report incorrect questions or explanations (feedback mechanism)
**FR8.6:** System displays explanation before showing reading content (logical flow)

### FR8.5: Post-Session Review (NEW)

**FR8.5.1:** System detects incorrect answers during session and flags for review
**FR8.5.2:** After session ends, system displays transition screen if incorrect answers exist
**FR8.5.3:** Transition screen shows session summary (X/Y correct) and review prompt
**FR8.5.4:** Users can choose to start review immediately or skip (optional but encouraged)
**FR8.5.5:** If skipped, system adds questions to spaced repetition schedule
**FR8.5.6:** Review presents each incorrect question again with "REVIEW" badge
**FR8.5.7:** System shows original answer vs correct answer as context
**FR8.5.8:** User re-answers question; system provides immediate feedback
**FR8.5.9:** System tracks "reinforcement": incorrect → correct on review
**FR8.5.10:** System shows explanation after each review answer
**FR8.5.11:** System displays review summary: "X reinforced correctly, Y still incorrect"
**FR8.5.12:** Summary shows improvement: "Original: 80% → Final: 93%"
**FR8.5.13:** System stores review data in `session_reviews` and `review_attempts` tables
**FR8.5.14:** Review contributes to competency updates (weighted appropriately)

### FR9: Asynchronous Reading Library (UPDATED)

**FR9.1:** System retrieves 2-3 relevant BABOK chunks **asynchronously** (background task) after each answer
**FR9.2:** Reading materials added to user's reading queue with priority (High/Medium/Low)
**FR9.3:** Priority calculated based on: user competency, was_incorrect, question difficulty
**FR9.4:** System updates navigation badge count **silently** (no popups/toasts) - e.g., [6] → [7]
**FR9.5:** **Zero interruption** to learning flow during quiz sessions
**FR9.6:** Reading Library accessible from main navigation anytime
**FR9.7:** Reading Library displays queue items sorted by priority (default)
**FR9.8:** Each item shows: title, BABOK section, KA, relevance score, priority, estimated read time
**FR9.9:** Each item shows context: which question prompted it, when added
**FR9.10:** Users can filter by: KA, priority, reading status (unread/reading/completed)
**FR9.11:** Users can search reading queue by keyword
**FR9.12:** Users can click "Read Now" to view full content in modal/page
**FR9.13:** System tracks engagement: times_opened, total_reading_time_seconds
**FR9.14:** Users can mark items as "Completed" or "Dismissed"
**FR9.15:** System supports bulk actions (dismiss multiple items)
**FR9.16:** Reading content includes: full markdown text, BABOK section, related question link
**FR9.17:** Users can rate reading helpfulness (thumbs up/down)
**FR9.18:** System displays reading stats: completion rate, total time, by KA breakdown
**FR9.19:** System prevents duplicate items (unique: user_id + chunk_id)
**FR9.20:** Reading queue stored in `reading_queue` table with all engagement metadata

### FR10: Spaced Repetition System

**FR10.1:** System tracks concept mastery for spaced repetition scheduling
**FR10.2:** System schedules concept reviews based on SM-2 algorithm (1, 3, 7, 14 day intervals)
**FR10.3:** System identifies when review questions are due (past scheduled date)
**FR10.4:** System creates mixed sessions: 40% reviews + 60% new when reviews are due
**FR10.5:** System labels review questions clearly ("Review" badge or indicator)
**FR10.6:** System updates review schedule based on review performance (correct = longer interval, incorrect = reset)
**FR10.7:** System prioritizes overdue reviews (past due date) over newly due reviews
**FR10.8:** System shows "Reviews Due" count on dashboard (motivational indicator)

### FR11: Progress Dashboard

**FR11.1:** Dashboard displays 6 KA competency bars with current scores (0-100% or equivalent scale)
**FR11.2:** Dashboard shows exam readiness score (overall preparedness indicator)
**FR11.3:** Dashboard displays reviews due count (number of concepts needing review)
**FR11.4:** Dashboard shows days until exam (countdown from onboarding exam date)
**FR11.5:** Dashboard displays weekly progress chart (competency changes over time)
**FR11.6:** Dashboard provides recommended focus areas (weakest KAs to study)
**FR11.7:** Dashboard shows total questions answered and reading content consumed
**FR11.8:** Dashboard includes primary action: "Continue Learning" or "Start Review"
**FR11.9:** Navigation includes Reading Library link with unread badge count (e.g., [7])
**FR11.10:** Badge shows high-priority indicator (red) if high-priority items exist
**FR11.11:** (Optional) Dashboard widget shows top 3 priority reading items

### FR12: Knowledge Area Detail View

**FR12.1:** Users can click/tap on a KA bar to view detailed competency breakdown
**FR12.2:** Detail view shows: current competency, target competency, gap, specific concept gaps
**FR12.3:** Detail view displays recent performance on this KA (last 10 questions)
**FR12.4:** Detail view shows time spent on this KA
**FR12.5:** Detail view provides action: "Study [KA Name]" to start focused session
**FR12.6:** System allows users to start KA-specific quiz sessions (focused learning)

### FR13: Settings & Preferences

**FR13.1:** Users can update profile information (name, email)
**FR13.2:** Users can update password
**FR13.3:** Users can update onboarding preferences (exam date, target score, study time)
**FR13.4:** Users can update notification preferences (if implemented)
**FR13.5:** Users can view privacy policy and terms of service
**FR13.6:** Users can export their data (responses, progress, study history)
**FR13.7:** Users can delete their account (with confirmation step)
**FR13.8:** Users can toggle between light mode, dark mode, or auto (system preference) - NEW MVP FEATURE
**FR13.9:** Dark mode preference persists across devices and sessions

### FR14: Question Bank Management (System)

**FR14.1:** System stores 500 gold standard vendor questions with metadata
**FR14.2:** System stores 500-1,000 LLM-generated question variations
**FR14.3:** All questions include: KA, difficulty level, concept tags, correct answer, explanations
**FR14.4:** System generates embeddings for all questions (semantic search capability)
**FR14.5:** System tracks question performance metrics (average correctness, user feedback)
**FR14.6:** System flags questions with poor metrics (< 50% or > 90% correctness, negative feedback)
**FR14.7:** System supports content updates (admin capability to add/edit/remove questions)

### FR15: Reading Content Management (System)

**FR15.1:** System stores BABOK v3 content parsed into chunks (200-500 tokens each)
**FR15.2:** All chunks include: KA, section reference, difficulty level, concept tags
**FR15.3:** System generates embeddings for all chunks (semantic similarity search)
**FR15.4:** System retrieves chunks via vector similarity based on question concepts and user gaps
**FR15.5:** System filters chunks by KA (only show relevant KA content)
**FR15.6:** System ranks chunks by relevance score (similarity + difficulty match)
**FR15.7:** System supports content updates (admin capability to re-chunk or update BABOK content)

### FR16: Data Persistence & Synchronization

**FR16.1:** System persists all user data in PostgreSQL database
**FR16.2:** System persists all question and reading embeddings in Qdrant vector database
**FR16.3:** System saves quiz progress in real-time (no data loss on browser close)
**FR16.4:** System synchronizes competency scores after every response
**FR16.5:** System maintains data consistency across user sessions
**FR16.6:** System handles concurrent sessions gracefully (same user, multiple devices)

### FR17: Error Handling & Recovery

**FR17.1:** System displays user-friendly error messages for failures
**FR17.2:** System logs errors for debugging without exposing technical details to user
**FR17.3:** System recovers from network errors gracefully (retry logic)
**FR17.4:** System prevents data loss during errors (save before operations)
**FR17.5:** System provides "Contact Support" option when errors occur
**FR17.6:** System shows loading indicators during operations (user feedback)

### FR18: Admin Operations and Support Tools

**FR18.1:** Admin users have elevated role flag (`is_admin: boolean`) stored in users table
**FR18.2:** Admin-only endpoints protected by `@require_admin` middleware (extends `@require_auth`)
**FR18.3:** Admin can search users by email, user_id, or name via GET `/api/admin/users/search?q={query}`
**FR18.4:** Search returns: user_id, email, created_at, onboarding_status, exam_date, last_login
**FR18.5:** Admin can impersonate any user via POST `/api/admin/impersonate/{user_id}`
**FR18.6:** Impersonation generates time-limited JWT (30 minutes) with `impersonated_by: admin_user_id` claim
**FR18.7:** Impersonated session shows banner: "Viewing as {user_email} | Exit Impersonation" (always visible)
**FR18.8:** Admin can exit impersonation anytime (returns to admin session)
**FR18.9:** All impersonation events logged to audit trail (admin_id, user_id, timestamp, duration)
**FR18.10:** User detail pages include PostHog deep link: "View in PostHog" → Opens PostHog profile for that user_id
**FR18.11:** PostHog integration configured with user_id as primary identifier (for linking)
**FR18.12:** Admin access restricted to designated admin users (cannot self-promote to admin)

---

## Non-Functional Requirements

### Performance

**Response Time Requirements:**
- **Page Load:** Initial app load < 3 seconds on 3G connection
- **Quiz Question Display:** < 500ms after answer submission
- **Competency Update:** < 1 second (real-time feel)
- **Reading Content Retrieval:** < 1 second (vector search + retrieval)
- **Dashboard Rendering:** < 2 seconds (with all charts and data)

**Throughput Requirements:**
- Support 10 concurrent users during MVP (case study + early testers)
- Support 100 concurrent users post-MVP (beta launch)
- Handle 1,000+ question retrievals per day
- Process 500+ answer submissions per day

**Scalability Target:**
- Architecture must support 10,000 users without redesign
- Database must handle millions of response records efficiently
- Vector database must scale to multiple certifications (10,000+ questions, 50,000+ chunks)

**Resource Usage:**
- Frontend bundle size < 500KB gzipped (fast downloads)
- API response payloads < 100KB (efficient data transfer)
- Minimize LLM API calls (use Llama locally when possible for cost)

**Rationale:** Study sessions are time-bound; slow responses frustrate users and break learning flow. Performance directly impacts user experience and retention.

### Security

**Authentication & Authorization:**
- Password hashing using bcrypt or Argon2 (strong, salted hashes)
- JWT tokens for session management with expiration (7 days)
- Secure session storage (HttpOnly cookies or secure storage)
- Rate limiting on authentication endpoints (prevent brute force)

**Data Protection:**
- Encryption in transit (HTTPS/TLS for all connections)
- Encryption at rest for sensitive data (passwords, PII)
- SQL injection prevention (parameterized queries, ORM)
- XSS prevention (input sanitization, output encoding)
- CSRF protection (tokens for state-changing operations)

**API Security:**
- Authentication required for all user-specific endpoints
- API rate limiting (prevent abuse)
- Input validation on all API endpoints
- Error messages do not leak system information

**Privacy & Compliance:**
- User data isolated (no cross-user data access)
- Admin access logging (audit trail for data access)
- Data deletion capability (GDPR right to be forgotten)
- Clear privacy policy and data usage documentation

**Admin Security:**
- Admin role assignment controlled via database flag (no API endpoint for promotion)
- Admin actions logged to audit trail for compliance and security review
- Impersonation tokens time-limited (30 minutes) to minimize risk window
- Impersonation restricted to non-admin users (admins cannot impersonate each other)
- Rate limiting on admin-sensitive operations (impersonation: 10/hour per admin)

**Rationale:** Users trust us with their learning data and career advancement. Security breaches would destroy trust and business viability.

### Scalability

**User Scalability:**
- MVP: 10 concurrent users (case study validation)
- Beta: 100 concurrent users (first cohort)
- GA: 1,000+ concurrent users (general availability)

**Data Scalability:**
- Support 10,000+ users with millions of response records
- Support 10,000+ questions across multiple certifications
- Support 50,000+ reading content chunks

**Content Scalability:**
- Architecture supports adding new certifications without major refactoring
- Question generation pipeline scales to produce thousands of variations
- Vector database supports multi-certification semantic search

**Infrastructure Scalability:**
- Horizontal scaling capability (add more servers)
- Database read replicas for query performance
- CDN for static assets (React bundle, images)
- Caching layer for frequently accessed data (Redis)

**Rationale:** Business model depends on multi-certification expansion. Architecture must support growth without costly rewrites.

### Accessibility

**WCAG 2.1 Level AA Compliance:**
- Keyboard navigation for all interactive elements (tab order, focus management)
- Screen reader compatibility (semantic HTML, ARIA labels, alt text)
- Color contrast ratios: 4.5:1 for normal text, 3:1 for large text
- Text resizing up to 200% without loss of functionality
- Focus indicators on all interactive elements (visible keyboard focus)
- No flashing content (avoid seizure triggers)
- Descriptive link text (not "click here")

**Responsive Design:**
- Mobile-friendly (portrait and landscape)
- Tablet-optimized (larger touch targets)
- Desktop-optimized (efficient use of space)

**Content Accessibility:**
- Plain language in UI (avoid jargon)
- Clear instructions and labels
- Error messages are descriptive and actionable
- Reading content formatted for readability (spacing, font size)

**Rationale:** Professional learners include people with disabilities. Accessibility is both ethical and expands market reach. WCAG Level AA is industry standard for quality web applications.

### Reliability & Availability

**Uptime Target:**
- MVP: 95% uptime (some downtime acceptable during development)
- GA: 99% uptime (< 7 hours downtime per month)

**Data Durability:**
- Zero data loss on user responses (all writes confirmed)
- Daily database backups with 30-day retention
- Point-in-time recovery capability (restore to any time in last 7 days)

**Error Recovery:**
- Graceful degradation (show cached data if API fails)
- Automatic retry for transient failures (network errors)
- User-friendly error messages with recovery options

**Monitoring & Alerting:**
- System health monitoring (API uptime, database performance)
- Error rate monitoring (alert on spike in errors)
- Performance monitoring (alert on slow responses)
- User activity monitoring (detect issues early)

**Rationale:** Users preparing for high-stakes exams depend on consistent access. Data loss or extended downtime damages trust and user outcomes.

### Maintainability & Testability

**Code Quality:**
- Clear code structure (modular, reusable components)
- Consistent coding standards (linting, formatting)
- Comprehensive documentation (inline comments, API docs)
- Type safety (TypeScript for frontend, type hints for Python backend)

**Testing Requirements:**
- Unit tests for business logic (competency estimation, spaced repetition)
- Integration tests for API endpoints (question retrieval, answer submission)
- End-to-end tests for critical user flows (onboarding, quiz, progress)
- Test coverage > 70% for business-critical code

**Deployment:**
- Automated deployment pipeline (CI/CD)
- Environment separation (local, staging, production)
- Database migration strategy (version-controlled schema changes)
- Rollback capability (revert to previous version if issues)

**Monitoring & Debugging:**
- Structured logging (JSON logs with context)
- Error tracking (Sentry or similar)
- Performance profiling capability
- User activity logs for debugging (anonymized)

**Rationale:** Rapid iteration is critical for MVP validation and post-launch improvements. Maintainability ensures development velocity. Testability ensures quality.

---

## Technical Assumptions

This section documents technical decisions that will guide the Architect. These choices are based on MVP constraints (30-day timeline, minimal budget), scalability requirements (multi-certification expansion), and alignment with project goals documented in the brief.

### Repository Structure: Monorepo

**Decision:** Use a **monorepo** structure for MVP to simplify coordination and enable shared types between frontend and backend.

**Repository Organization:**
- `/frontend` - React web application (TypeScript)
- `/backend` - FastAPI application (Python 3.11+)
- `/shared` - Shared types/interfaces (TypeScript type definitions, Pydantic models)
- `/scripts` - Content generation pipelines, embedding generation, BABOK parsing, admin utilities
- `/docs` - Architecture docs, API specs, deployment guides, decision logs

**Rationale:**
- Faster iteration during MVP (single git repo, coordinated releases)
- Shared types reduce bugs at API boundaries (TypeScript + Pydantic model sync)
- Simpler CI/CD setup (single pipeline for entire system)
- Team size (small MVP team) doesn't justify multi-repo overhead

**Alternative Considered:** Multi-repo (separate frontend and backend repositories) - Better for larger teams with independent release cycles, but adds coordination overhead unnecessary for MVP.

**Post-MVP Evolution:** Can split into multi-repo if team grows or independent release cadences needed.

### Service Architecture: Monolithic Backend

**Decision:** Build a **monolithic FastAPI backend** service containing all features for MVP, with optional microservices extraction post-validation.

**Monolithic Service Architecture:**
- Single FastAPI application handling:
  - Authentication & user management
  - Quiz engine (diagnostic, adaptive question selection, session management)
  - Competency tracking & IRT calculations
  - Reading content retrieval (vector search against Qdrant)
  - Spaced repetition scheduling
  - Progress tracking & analytics
- RESTful JSON API endpoints
- Async request handling (FastAPI async/await)
- SQLAlchemy ORM for PostgreSQL operations
- Qdrant client for vector database queries

**Rationale:**
- Faster development (no inter-service communication complexity)
- Simpler deployment (single container/process)
- Acceptable performance for MVP scale (10-100 concurrent users)
- Easier debugging and local development
- Can handle 1,000+ users before bottlenecks emerge

**When to Consider Microservices (Post-MVP):**
- Only if monolith becomes performance bottleneck (>1,000 concurrent users)
- Potential service boundaries:
  - **Auth Service:** User authentication, session management
  - **Quiz Service:** Question selection, competency tracking, adaptive algorithm
  - **Content Service:** Vector search, BABOK retrieval, question bank management
  - **Analytics Service:** Progress tracking, KPI calculation, reporting

**Current Decision:** Defer microservices until scale demands; premature optimization would slow MVP delivery.

### API Versioning Strategy: /v1/ Prefix for Future Compatibility

**Decision:** All API endpoints use `/v1/` prefix for version compatibility and future evolution (e.g., `POST /v1/quiz/answer` not `POST /api/quiz/answer`).

**API Path Format:**
- Authentication: `POST /v1/auth/login`, `POST /v1/auth/register`, `POST /v1/auth/logout`
- Quiz: `POST /v1/quiz/answer`, `GET /v1/quiz/session/{session_id}`
- Reading: `GET /v1/reading/queue`, `POST /v1/reading/queue/batch-dismiss`, `GET /v1/reading/stats`
- User: `GET /v1/user/profile`, `PUT /v1/user/profile`, `POST /v1/user/change-password`
- Content: `POST /v1/content/search`, `GET /v1/content/chunks/{chunk_id}`
- Admin: `GET /v1/admin/users/search`, `POST /v1/admin/impersonate/{user_id}`

**Rationale:**
- **Future-proofing:** Allows backward-compatible API evolution (v1 stays stable, v2 introduces breaking changes)
- **Client flexibility:** Clients can specify which version they support
- **Clear versioning contract:** Version in URL makes compatibility explicit
- **Industry standard:** REST API best practice for long-lived applications

**Version Deprecation Strategy (Post-MVP):**
- When introducing breaking changes: Launch `/v2/` endpoints alongside `/v1/`
- Support overlap period: Both versions active for 6 months
- Deprecation notice: Return `X-API-Deprecated: v1 will sunset on YYYY-MM-DD` header
- Final cutover: Disable v1 endpoints after transition period

**Current Version:** v1 (MVP launch)

**Note:** All API endpoint references in this PRD use `/v1/` prefix. Supporting documentation may use `/api/` as shorthand, but implementation must use versioned paths.

### Testing Requirements: Unit + Integration Testing for Business-Critical Code

**Decision:** Implement **Unit + Integration testing** focused on business-critical code paths, with manual E2E testing for MVP.

**Testing Pyramid for MVP:**

**1. Unit Tests (Foundation):**
- **Backend Business Logic:**
  - Competency estimation (IRT algorithm) - CRITICAL
  - Adaptive question selection logic - CRITICAL
  - Spaced repetition scheduling (SM-2 algorithm) - CRITICAL
  - User data validation (Pydantic models)
  - Content retrieval ranking logic
- **Frontend Components (Selective):**
  - Critical user flows (question answering, explanation display)
  - Data visualization components (competency bars, progress charts)
- **Coverage Target:** >70% for business-critical modules
- **Tool:** pytest (backend), Jest/React Testing Library (frontend)

**2. Integration Tests (API Level):**
- **Backend API Endpoints:**
  - POST /diagnostic - Diagnostic submission + competency calculation
  - POST /quiz/session - Start adaptive quiz session
  - POST /quiz/answer - Submit answer + update competency + retrieve reading
  - GET /progress - Dashboard data retrieval
  - POST /auth/login - Authentication flow
- **Database Integrations:**
  - PostgreSQL read/write operations (user data, responses, competency tracking)
  - Qdrant vector search (question retrieval, reading chunk retrieval)
- **Coverage Target:** All critical API endpoints tested
- **Tool:** pytest with test database, Qdrant test collection

**3. End-to-End Tests (Manual for MVP):**
- **Critical User Journeys (Manual Testing):**
  - Onboarding → Diagnostic → Results → Dashboard (first-time user flow)
  - Quiz session → Answer → Explanation → Reading → Next question (learning loop)
  - Spaced repetition: Review due → Mixed session → Review accuracy tracking
  - Settings: Update exam date, password reset, account deletion
- **Why Manual for MVP:** E2E automation (Playwright, Cypress) takes time; manual testing acceptable for 30-day sprint
- **Post-MVP:** Automate E2E tests for regression prevention during beta

**Testing Philosophy:**
- **Test behavior, not implementation** (black-box approach where possible)
- **Focus on business value** (competency accuracy > UI styling)
- **Fast feedback loops** (unit tests run in <5 seconds for rapid iteration)
- **CI Integration** (tests run on every commit; block merge if critical tests fail)

**Explicit Non-Testing for MVP:**
- Performance/load testing (defer until beta scale)
- Security penetration testing (basic security practices enforced, formal testing post-MVP)
- Accessibility automated testing (manual WCAG compliance verification, automated tools in Phase 2)

### Additional Technical Assumptions and Requests

Throughout the PRD development and brief analysis, these additional technical assumptions have been identified as critical for the Architect:

**1. Data Model Assumptions:**
- **Competency Tracking:** Per-user, per-KA competency scores stored with timestamp history (enables weekly progress trends)
- **Spaced Repetition State:** Per-user, per-concept tracking (last_seen, next_review_date, ease_factor, interval, repetition_count)
- **Response History:** All user answers persisted with metadata (question_id, answer_selected, correctness, time_taken, timestamp, session_id)
- **Session Management:** Quiz sessions track start/end times, questions answered, paused state (enable resume capability)

**2. API Design Assumptions:**
- **RESTful conventions:** Standard HTTP methods (GET, POST, PUT, DELETE), status codes (200, 201, 400, 401, 404, 500)
- **JSON request/response:** All API communication uses JSON (no XML, form-encoded)
- **Stateless API:** JWT tokens carry authentication; no server-side session state (enables horizontal scaling)
- **Pagination:** Not needed for MVP (small data sets per user), defer to Phase 2 if needed

**3. Frontend State Management:**
- **Decision Deferred to Architect:** React Context API vs. Redux Toolkit
- **Recommendation:** Context API sufficient for MVP (simpler, less boilerplate)
- **When Redux Needed:** If state management becomes unwieldy or performance issues arise (complex cross-component state)

**4. Deployment & Infrastructure:**
- **MVP Hosting:**
  - Frontend: Vercel or Netlify (free tier, CDN included, simple deployment)
  - Backend: Railway or Render (container deployment, ~$20/month)
  - PostgreSQL: Managed service from Railway/Render ($10-15/month)
  - Qdrant: Self-hosted via Docker on backend server (cost $0)
- **CI/CD:** GitHub Actions (free for public repos, included in GitHub plan)
- **Environment Variables:** Secure storage for API keys (OpenAI, database URLs, JWT secrets)

**5. Content Processing Pipeline:**
- **BABOK Parsing:** PyMuPDF or pdfplumber for PDF text extraction
- **Chunking Strategy:** Hybrid structural + semantic chunking (200-500 tokens, respect section boundaries)
- **Embedding Generation:** Batch process (all questions + chunks upfront, minimal ongoing costs)
- **Question Generation:** GPT-4 for quality baseline, Llama 3.1 for volume variations (cost optimization)

**6. Security & Privacy:**
- **Password Hashing:** bcrypt or Argon2 (industry standard, salted hashes)
- **JWT Expiration:** 7-day token expiration, refresh token strategy for longer sessions
- **HTTPS Only:** All production traffic over TLS (no HTTP endpoints)
- **Input Validation:** Pydantic models validate all API inputs (prevent injection attacks)
- **Rate Limiting:** Implement on auth endpoints (prevent brute force), defer for other endpoints until abuse detected

**7. Performance Assumptions:**
- **Response Time Targets:**
  - Question display: <500ms after answer submission
  - Reading content retrieval: <1 second (vector search + PostgreSQL join)
  - Dashboard rendering: <2 seconds (aggregate all 6 KA scores + trends)
- **Database Queries:** Indexed on user_id, question_id, session_id for fast lookups
- **Caching:** Not implemented in MVP (premature optimization), consider Redis post-MVP if needed

**8. Monitoring & Observability (Minimal for MVP):**
- **Error Tracking:** Sentry or similar for backend exceptions
- **Logging:** Structured JSON logs (timestamp, user_id, endpoint, error details)
- **Analytics:** Minimal (user count, session count), no invasive tracking
- **Post-MVP:** Add performance monitoring (response times), user analytics (Plausible or similar)

**9. Known Technical Debt Accepted for MVP:**
- Simplified IRT (not full 3-parameter IRT with item calibration)
- Manual E2E testing (no automation)

### Supporting Technical Documentation (REQUIRED READING)

**CRITICAL:** This PRD is supported by detailed technical specifications that provide implementation-level guidance. Architects, UX designers, and developers MUST review these documents alongside the PRD for complete understanding:

**v2.1 Feature Specifications:**
- **`docs/Implementation_Summary.md`** (964 lines) - Master implementation guide for Post-Session Review and Asynchronous Reading Library features
- **`docs/Asynchronous_Reading_Model.md`** (1,050 lines) - Complete technical architecture for the reading queue system, including data models, API contracts, and UX specifications
- **`docs/Learning_Loop_Refinement.md`** (1,488 lines) - Detailed specification of the post-session review feature with flowcharts and phase-by-phase implementation guidance

**UX/UI Specifications:**
- **`docs/front-end-spec.md`** (1,801 lines) - Complete UI/UX specification including information architecture, design system, component specs, and accessibility requirements
- **`docs/user-flows.md`** (747 lines) - Detailed user flow diagrams (Mermaid format) covering onboarding, learning loops, review flows, and reading library interactions

**Cross-Reference Notes:**
- Epic 4 Stories 4.6-4.9 (Post-Session Review) → See `Learning_Loop_Refinement.md` Phase 2 specification
- Epic 5 Stories 5.5-5.9 (Async Reading Library) → See `Asynchronous_Reading_Model.md` for complete architecture
- All UI implementation → Reference `front-end-spec.md` for design system tokens, component specifications, and accessibility requirements
- All user flows → See `user-flows.md` Flows 4, 4b, and 9 for detailed interaction diagrams

---

## Epic List

This section presents the high-level epic structure for LearnR MVP implementation. Each epic delivers a significant, end-to-end increment of testable functionality following agile best practices. Epics are sequenced to enable incremental delivery while building toward the complete adaptive learning platform.

### Epic Overview

**Epic 1: Foundation & User Authentication**
**Goal:** Establish project infrastructure, development environment, and secure user authentication system with basic user management capabilities.

Delivers: Working monorepo with CI/CD, PostgreSQL database, user registration/login, password management, and project health-check endpoint demonstrating full-stack integration.

---

**Epic 2: Content Foundation & Question Bank**
**Goal:** Build the content processing pipeline and establish the question bank with embeddings, enabling the platform to serve CBAP questions.

Delivers: 600-1,000 questions loaded with metadata, BABOK v3 parsed and chunked, all content embedded in Qdrant, content retrieval APIs functional and testable.

---

**Epic 3: Diagnostic Assessment & Competency Baseline**
**Goal:** Enable users to complete the 12-question diagnostic assessment and receive accurate baseline competency scores across all 6 CBAP knowledge areas.

Delivers: Anonymous onboarding flow (7 questions), account creation, 12-question diagnostic quiz interface (3 per KA), simplified IRT competency calculation, diagnostic results screen with KA breakdown and gap analysis.

---

**Epic 4: Adaptive Quiz Engine & Explanations**
**Goal:** Implement the core adaptive learning loop with intelligent question selection, answer submission, and detailed explanations.

Delivers: Adaptive quiz sessions with real-time competency updates, difficulty matching, immediate feedback, comprehensive explanations with user feedback capability.

---

**Epic 5: Targeted Reading Content Integration**
**Goal:** Complete the learning loop by adding semantic BABOK content retrieval that addresses user-specific knowledge gaps (critical differentiator).

Delivers: Vector search retrieval of relevant BABOK chunks, reading content display after explanations, reading engagement tracking, validation of differentiation value.

---

**Epic 6: Progress Dashboard & Transparency**
**Goal:** Provide users with comprehensive progress visibility through real-time competency tracking, exam readiness scoring, and actionable recommendations.

Delivers: Dashboard with 6 KA competency bars, exam readiness score, weekly progress trends, KA detail views, days-until-exam countdown, recommended focus areas.

---

**Epic 7: Spaced Repetition & Long-Term Retention**
**Goal:** Implement SM-2 spaced repetition system to ensure users retain learned concepts through exam day.

Delivers: Concept mastery tracking, review scheduling (1/3/7/14 day intervals), mixed quiz sessions (reviews + new content), review performance tracking, reviews-due indicator on dashboard.

---

**Epic 8: Polish, Testing & Launch Readiness**
**Goal:** Complete platform polish, comprehensive testing, performance optimization, and deployment for case study user validation.

Delivers: Settings/profile management, accessibility compliance (WCAG 2.1 AA), error handling, production deployment, alpha test readiness, all acceptance criteria validated.

---

### Epic Sequencing Rationale

**Why This Structure:**

1. **Epic 1** establishes technical foundation (monorepo, database, CI/CD) while delivering initial user capability (authentication) - demonstrates full-stack integration early

2. **Epic 2** loads all content (questions + BABOK) before building features that consume it - enables all subsequent epics to have real data

3. **Epic 3** builds diagnostic first because competency baseline is required for adaptive algorithm (Epic 4) to function

4. **Epic 4** creates core quiz experience before adding reading content (Epic 5) - validates basic adaptive loop works

5. **Epic 5** adds critical differentiator (reading content) mid-sprint to allow Day 24 alpha test validation

6. **Epic 6** provides progress visibility after core learning loop functional - users need quiz capability before progress makes sense

7. **Epic 7** adds spaced repetition after quiz working - review scheduling requires existing question history

8. **Epic 8** focuses on polish and deployment after all features functional - prepares for production launch

**Incremental Value Delivery:**
- After Epic 1: Team can develop and deploy code
- After Epic 2: Content is loaded and queryable
- After Epic 3: Users can take diagnostic and see competency scores
- After Epic 4: Users can study adaptively with explanations
- After Epic 5: **CRITICAL - Alpha test can validate reading differentiation (Day 24 Go/No-Go)**
- After Epic 6: Users have full progress transparency
- After Epic 7: Retention system ensures long-term learning
- After Epic 8: Platform ready for production case study validation

---

## Database Schema Summary

This section provides complete SQL DDL statements for all LearnR database tables. All tables use PostgreSQL 15+.

**Schema Design Principles:**
- UUIDs for all primary keys (distributed-system ready, avoid sequential ID leakage)
- Timestamps: `created_at`, `updated_at` on all tables (audit trail)
- Foreign key constraints with CASCADE deletes where appropriate (user deletion cleanup)
- Indexes on frequently queried fields (user_id, session_id, KA filters, reading_status)
- JSONB columns for flexible metadata (PostHog properties, admin action details)

### Core Tables (v2.0 Foundation)

#### Table: `users`
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE, -- v2.2: Admin role flag
    theme_preference VARCHAR(10) DEFAULT 'auto', -- v2.2: 'light' | 'dark' | 'auto'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_admin ON users(is_admin) WHERE is_admin = TRUE;
```

#### Table: `onboarding_data`
```sql
CREATE TABLE onboarding_data (
    onboarding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referral_source VARCHAR(50), -- 'search' | 'referral' | 'social' | 'other'
    certification VARCHAR(50) NOT NULL, -- 'CBAP' for MVP
    motivation VARCHAR(100), -- 'career_advancement' | 'salary' | 'credibility' | etc
    exam_date DATE NOT NULL,
    knowledge_level VARCHAR(20), -- 'beginner' | 'intermediate' | 'advanced'
    target_score VARCHAR(10), -- 'pass' | 'high_pass' (70% | 80% | 90%)
    daily_commitment VARCHAR(20), -- '30-60min' | '1-2hrs' | '2+hrs'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_onboarding_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_onboarding_user ON onboarding_data(user_id);
```

#### Table: `questions`
```sql
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer CHAR(1) NOT NULL CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    explanation TEXT NOT NULL, -- Max 200 characters (enforced in application)
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    difficulty DECIMAL(3,2) NOT NULL CHECK (difficulty >= 0 AND difficulty <= 1),
    concept_tags JSONB, -- Array of concept tags for semantic search
    source VARCHAR(50), -- 'vendor' | 'llm_generated'
    babok_section VARCHAR(20), -- e.g., "3.2.1"
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_ka ON questions(ka_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_concept_tags ON questions USING GIN(concept_tags);
```

#### Table: `content_chunks`
```sql
CREATE TABLE content_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    section_ref VARCHAR(20), -- BABOK section reference (e.g., "3.2.1")
    title VARCHAR(255),
    text_content TEXT NOT NULL, -- 200-500 tokens per chunk
    word_count INT NOT NULL,
    difficulty VARCHAR(20), -- 'easy' | 'medium' | 'hard'
    concept_tags JSONB, -- Array of concept tags
    embedding VECTOR(1536), -- OpenAI text-embedding-3-large dimensions
    page_reference INT, -- Page number in BABOK v3
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_ka ON content_chunks(ka_id);
CREATE INDEX idx_chunks_embedding ON content_chunks USING ivfflat(embedding vector_cosine_ops);
```

#### Table: `knowledge_areas`
```sql
CREATE TABLE knowledge_areas (
    ka_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ka_name VARCHAR(255) NOT NULL UNIQUE,
    ka_abbreviation VARCHAR(10), -- e.g., "BAPM"
    description TEXT,
    display_order INT NOT NULL
);

-- Pre-populate with 6 CBAP Knowledge Areas
INSERT INTO knowledge_areas (ka_name, ka_abbreviation, display_order) VALUES
('Business Analysis Planning and Monitoring', 'BAPM', 1),
('Elicitation and Collaboration', 'EC', 2),
('Requirements Life Cycle Management', 'RLCM', 3),
('Strategy Analysis', 'SA', 4),
('Requirements Analysis and Design Definition', 'RADD', 5),
('Solution Evaluation', 'SE', 6);
```

#### Table: `competency_tracking`
```sql
CREATE TABLE competency_tracking (
    competency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ka_id UUID NOT NULL REFERENCES knowledge_areas(ka_id),
    competency_score DECIMAL(4,2) NOT NULL CHECK (competency_score >= 0 AND competency_score <= 100),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_ka UNIQUE (user_id, ka_id)
);

CREATE INDEX idx_competency_user ON competency_tracking(user_id);
CREATE INDEX idx_competency_ka ON competency_tracking(ka_id);
```

#### Table: `quiz_sessions`
```sql
CREATE TABLE quiz_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_type VARCHAR(20) NOT NULL, -- 'diagnostic' | 'adaptive' | 'review' | 'mixed'
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_questions INT DEFAULT 0,
    correct_count INT DEFAULT 0,
    session_status VARCHAR(20) DEFAULT 'active' -- 'active' | 'completed' | 'abandoned'
);

CREATE INDEX idx_sessions_user ON quiz_sessions(user_id);
CREATE INDEX idx_sessions_status ON quiz_sessions(session_status);
```

#### Table: `quiz_responses`
```sql
CREATE TABLE quiz_responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    selected_answer CHAR(1) NOT NULL CHECK (selected_answer IN ('A', 'B', 'C', 'D')),
    is_correct BOOLEAN NOT NULL,
    time_spent_seconds INT,
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responses_session ON quiz_responses(session_id);
CREATE INDEX idx_responses_user ON quiz_responses(user_id);
CREATE INDEX idx_responses_question ON quiz_responses(question_id);
```

### v2.1 New Tables (Reading Library & Post-Session Review)

#### Table: `reading_queue` (Epic 5)
```sql
CREATE TABLE reading_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,

    -- Context: Why was this recommended?
    question_id UUID REFERENCES questions(question_id) ON DELETE SET NULL,
    session_id UUID REFERENCES quiz_sessions(session_id) ON DELETE SET NULL,
    was_incorrect BOOLEAN DEFAULT TRUE,

    -- Priority & Relevance
    relevance_score DECIMAL(3,2) NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
    ka_id UUID REFERENCES knowledge_areas(ka_id) ON DELETE SET NULL,

    -- Reading State
    reading_status VARCHAR(20) DEFAULT 'unread' CHECK (reading_status IN ('unread', 'reading', 'completed', 'dismissed')),

    -- Engagement Tracking
    times_opened INT DEFAULT 0,
    total_reading_time_seconds INT DEFAULT 0,
    first_opened_at TIMESTAMP,
    completed_at TIMESTAMP,
    dismissed_at TIMESTAMP,

    -- Timestamps
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reading_queue_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_reading_queue_chunk FOREIGN KEY (chunk_id) REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,
    CONSTRAINT unique_user_chunk_queue UNIQUE (user_id, chunk_id)
);

CREATE INDEX idx_reading_queue_user_status ON reading_queue(user_id, reading_status);
CREATE INDEX idx_reading_queue_user_unread ON reading_queue(user_id, reading_status) WHERE reading_status = 'unread';
CREATE INDEX idx_reading_queue_ka ON reading_queue(ka_id);
CREATE INDEX idx_reading_queue_priority ON reading_queue(user_id, priority, reading_status);
```

**Field Explanations:**
- `relevance_score`: Semantic similarity between question and chunk (0.00-1.00)
- `priority`: Calculated based on user competency gap, mistake frequency, and recency
- `reading_status`: User interaction state (unread → reading → completed/dismissed)
- `times_opened`: Tracks if user revisits material (engagement metric)

#### Table: `session_reviews` (Epic 4)
```sql
CREATE TABLE session_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_progress', 'completed', 'skipped')),
    items_to_review INT NOT NULL,
    items_reviewed INT DEFAULT 0,
    improvement_rate DECIMAL(4,2), -- % of incorrect → correct (0.00-1.00)
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_reviews_user ON session_reviews(user_id);
CREATE INDEX idx_session_reviews_session ON session_reviews(session_id);
CREATE INDEX idx_session_reviews_status ON session_reviews(review_status);
```

#### Table: `review_attempts` (Epic 4)
```sql
CREATE TABLE review_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES session_reviews(review_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    original_answer CHAR(1) NOT NULL CHECK (original_answer IN ('A', 'B', 'C', 'D')),
    review_answer CHAR(1) NOT NULL CHECK (review_answer IN ('A', 'B', 'C', 'D')),
    now_correct BOOLEAN NOT NULL,
    attempt_number INT DEFAULT 1,
    time_spent_seconds INT,
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_attempts_review ON review_attempts(review_id);
CREATE INDEX idx_review_attempts_question ON review_attempts(question_id);
```

### v2.2 New Tables (Admin & Analytics)

#### Table: `admin_audit_log` (Epic 8)
```sql
CREATE TABLE admin_audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES users(user_id),
    action_type VARCHAR(50) NOT NULL, -- 'impersonation_started' | 'impersonation_ended' | 'user_search' | etc
    target_user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    metadata JSONB, -- {duration_seconds, ip_address, user_agent, etc}
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_admin ON admin_audit_log(admin_user_id);
CREATE INDEX idx_audit_target ON admin_audit_log(target_user_id);
CREATE INDEX idx_audit_action ON admin_audit_log(action_type);
CREATE INDEX idx_audit_timestamp ON admin_audit_log(created_at DESC);
```

### Spaced Repetition Tables (Epic 7)

#### Table: `concept_mastery`
```sql
CREATE TABLE concept_mastery (
    mastery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    concept_tag VARCHAR(100) NOT NULL,
    ka_id UUID REFERENCES knowledge_areas(ka_id),
    mastery_level INT DEFAULT 0 CHECK (mastery_level >= 0 AND mastery_level <= 5),
    last_reviewed_at TIMESTAMP,
    next_review_at TIMESTAMP,
    review_count INT DEFAULT 0,
    correct_streak INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_concept UNIQUE (user_id, concept_tag)
);

CREATE INDEX idx_mastery_user ON concept_mastery(user_id);
CREATE INDEX idx_mastery_next_review ON concept_mastery(user_id, next_review_at);
CREATE INDEX idx_mastery_ka ON concept_mastery(ka_id);
```

#### Table: `spaced_repetition_schedule`
```sql
CREATE TABLE spaced_repetition_schedule (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    concept_tag VARCHAR(100) NOT NULL,
    next_review_date DATE NOT NULL,
    review_interval_days INT NOT NULL, -- 1, 3, 7, 14 (SM-2 adapted)
    ease_factor DECIMAL(3,2) DEFAULT 2.50,
    consecutive_correct INT DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_question_srs UNIQUE (user_id, question_id)
);

CREATE INDEX idx_srs_user_date ON spaced_repetition_schedule(user_id, next_review_date);
CREATE INDEX idx_srs_concept ON spaced_repetition_schedule(concept_tag);
```

### Engagement & Feedback Tables

#### Table: `explanation_feedback`
```sql
CREATE TABLE explanation_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    helpful BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_explanation_feedback_question ON explanation_feedback(question_id);
```

#### Table: `question_reports`
```sql
CREATE TABLE question_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id),
    issue_type VARCHAR(50) NOT NULL, -- 'incorrect_question' | 'unclear_explanation' | 'typo' | etc
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'resolved', 'dismissed')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_status ON question_reports(status);
CREATE INDEX idx_reports_question ON question_reports(question_id);
```

---

## Algorithm Specifications

LearnR's adaptive learning engine relies on several key algorithms. This section provides complete pseudocode for implementation.

**Algorithm Design Principles:**
- **Start simple, refine iteratively:** MVP uses simplified formulas (e.g., fixed competency deltas); Phase 2 can implement full IRT
- **Transparent to users:** Competency scores and progress always visible, not "black box" AI
- **Tunable parameters:** Key thresholds and weights configurable for A/B testing post-MVP
- **Performance-conscious:** All algorithms execute in <500ms to maintain responsive UX

---

### Algorithm 1: Priority Calculation for Reading Materials

**Purpose:** Determines High/Medium/Low priority for reading queue items based on user performance and competency.

**Trigger:** When adding content to reading queue (after incorrect answer or low competency)

**Parameters:**
- `user_competency` (float): Overall user competency (0.0-1.0)
- `was_incorrect` (boolean): Whether user answered question incorrectly
- `ka_competency` (float): User's competency in this specific Knowledge Area (0.0-1.0)
- `question_difficulty` (float): Question difficulty level (0.0-1.0)

**Returns:** `'high'` | `'medium'` | `'low'`

**Pseudocode:**
```python
def calculate_priority(
    user_competency: float,
    was_incorrect: bool,
    ka_competency: float,
    question_difficulty: float
) -> str:
    """
    Calculate reading priority based on multiple factors.

    Key Thresholds:
    - KA competency < 0.5: High priority (significant gap)
    - KA competency < 0.6: High priority if incorrect
    - Question difficulty > 0.5: High priority if incorrect
    - KA competency 0.6-0.75: Medium priority (borderline)
    - KA competency > 0.75: Low priority (proficient)
    """

    # High priority conditions:
    # - User got question wrong AND has significant gap in this KA
    if was_incorrect and ka_competency < 0.6:
        return 'high'

    # - User got question wrong AND question was moderately difficult
    if was_incorrect and question_difficulty > 0.5:
        return 'high'

    # - User has major competency gap regardless of answer
    if ka_competency < 0.5:
        return 'high'

    # Medium priority:
    # - User got question wrong but competency is okay
    if was_incorrect:
        return 'medium'

    # - User's competency is borderline (needs reinforcement)
    if 0.6 <= ka_competency < 0.75:
        return 'medium'

    # Low priority:
    # - User got question right AND competency already good
    return 'low'
```

**Example Scenarios:**
- User with KA competency 0.45 answers incorrectly → **High** (significant gap + mistake)
- User with KA competency 0.68 answers incorrectly → **Medium** (borderline competency)
- User with KA competency 0.82 answers correctly → **Low** (proficient)

---

### Algorithm 2: Asynchronous Reading Queue Population

**Purpose:** Automatically add relevant BABOK reading chunks to user's queue after answering questions.

**Trigger:** After each question answered (if incorrect OR if user's KA competency < 0.7)

**Parameters:**
- `user_id`: UUID of user
- `question_id`: UUID of question just answered
- `session_id`: UUID of current quiz session
- `ka_id`: UUID of Knowledge Area
- `user_competency`: User's current competency in this KA (0.0-1.0)
- `was_incorrect`: Whether answer was incorrect

**Implementation:** Runs asynchronously (background task/queue) to avoid blocking quiz response

**Pseudocode:**
```python
async def add_reading_to_queue_async(
    user_id: UUID,
    question_id: UUID,
    session_id: UUID,
    ka_id: UUID,
    user_competency: float,
    was_incorrect: bool
) -> None:
    """
    Asynchronously add relevant reading material to user's queue.

    Steps:
    1. Get question details and concept tags
    2. Build semantic query from question + tags
    3. Vector similarity search for relevant chunks
    4. Calculate priority
    5. Add to queue (top 2-3 chunks, avoid duplicates)
    6. Notify user (update badge count)
    """

    # Step 1: Get question details
    question = await db.get_question(question_id)

    # Step 2: Build semantic query
    # Combine question text with concept tags for richer semantic match
    query_text = f"{question.question_text} {' '.join(question.concept_tags)}"
    query_embedding = await get_embedding(query_text)  # OpenAI API call

    # Step 3: Vector similarity search
    # Find top 3 most semantically similar chunks in same KA
    chunks = await db.query(ContentChunk)\
        .filter(ContentChunk.ka_id == ka_id)\
        .order_by(
            ContentChunk.embedding.cosine_distance(query_embedding).asc()
        )\
        .limit(3)\
        .all()

    # Step 4: Calculate priority for these chunks
    priority = calculate_priority(
        user_competency=user_competency,
        was_incorrect=was_incorrect,
        ka_competency=user_competency,
        question_difficulty=question.difficulty
    )

    # Step 5: Add to queue (with duplicate prevention)
    for chunk in chunks:
        # Calculate relevance score (1.0 = perfect match, 0.0 = no match)
        relevance_score = 1 - cosine_distance(chunk.embedding, query_embedding)

        # Only add if sufficiently relevant (threshold: 0.7)
        if relevance_score > 0.7:
            # Check if chunk already in user's queue
            existing = await db.get_reading_queue_item(user_id, chunk.chunk_id)

            if not existing:
                # Add new reading queue item
                reading_item = ReadingQueue(
                    user_id=user_id,
                    chunk_id=chunk.chunk_id,
                    question_id=question_id,
                    session_id=session_id,
                    was_incorrect=was_incorrect,
                    relevance_score=round(relevance_score, 2),
                    priority=priority,
                    ka_id=ka_id,
                    reading_status='unread',
                    added_at=datetime.now()
                )
                await db.add(reading_item)

    await db.commit()

    # Step 6: Update user's unread badge count
    # Send real-time notification (WebSocket/SSE) or set flag for next page load
    await notify_user_reading_added(user_id)
```

**Performance Notes:**
- OpenAI embedding API call: ~100-200ms
- Vector similarity search (Qdrant or pgvector): ~50-150ms
- Database inserts: ~20-50ms
- **Total estimated time:** 200-400ms (acceptable for background task)

**Relevance Threshold Rationale:**
- 0.7 threshold filters out weakly related content
- Typical distribution: Top 1-2 chunks score 0.8-0.95, next 1-2 score 0.7-0.8
- Prevents queue pollution with marginally relevant material

---

### Algorithm 3: Simplified IRT Competency Update

**Purpose:** Update user's competency score after each quiz answer using simplified Item Response Theory.

**Trigger:** After each quiz answer submission

**Parameters:**
- `current_competency`: User's current competency in this KA (0.0-100.0)
- `question_difficulty`: Question difficulty (0.0-1.0 scale)
- `is_correct`: Whether answer was correct

**Returns:** Updated competency score (0.0-100.0)

**Pseudocode:**
```python
def update_competency_simple_irt(
    current_competency: float,
    question_difficulty: float,
    is_correct: bool
) -> float:
    """
    Simplified IRT competency update for MVP.

    Logic:
    - Harder questions answered correctly → larger boost
    - Easier questions answered correctly → smaller boost
    - Any incorrect answer → small penalty (-1%)
    - Competency capped at 0-100%

    Phase 2: Replace with full IRT using logistic model
    """

    # Map difficulty to competency delta
    if is_correct:
        if question_difficulty >= 0.7:  # Hard question
            delta = +5.0
        elif question_difficulty >= 0.4:  # Medium question
            delta = +3.0
        else:  # Easy question
            delta = +2.0
    else:
        # Small penalty for incorrect (prevents overconfidence)
        delta = -1.0

    # Apply delta
    new_competency = current_competency + delta

    # Clamp to valid range
    new_competency = max(0.0, min(100.0, new_competency))

    return new_competency
```

**Example Updates:**
- User at 60% competency answers Hard question correctly → 65% (+5%)
- User at 75% competency answers Easy question correctly → 77% (+2%)
- User at 80% competency answers Medium question incorrectly → 79% (-1%)

**Phase 2 Enhancement (Post-MVP):**
Replace with full IRT logistic model:
```
P(correct) = 1 / (1 + e^(-a * (θ - b)))
where:
  θ = user ability (competency)
  b = question difficulty
  a = question discrimination
```

---

### Algorithm 4: Adaptive Question Selection

**Purpose:** Select next question based on user's competency, gaps, and question history.

**Trigger:** When user clicks "Next Question" or starts new session

**Parameters:**
- `user_id`: UUID of user
- `session_id`: UUID of current session
- `target_ka_id` (optional): If user selected focused KA practice

**Selection Criteria (prioritized):**
1. **KA Match:** If `target_ka_id` specified, only select from that KA
2. **Gap Targeting:** Prefer KAs where user competency < 70%
3. **Difficulty Targeting:** Select difficulty near user's competency level (±10%)
4. **Freshness:** Avoid questions answered in last 7 days (if possible)
5. **Randomization:** Shuffle eligible questions to avoid patterns

**Pseudocode:**
```python
def select_next_question(
    user_id: UUID,
    session_id: UUID,
    target_ka_id: Optional[UUID] = None
) -> Question:
    """
    Select next adaptive question using multi-criteria filtering.
    """

    # Get user's competency across all KAs
    competencies = db.get_user_competencies(user_id)

    # Determine target KA
    if target_ka_id:
        ka_id = target_ka_id
        user_competency = competencies[ka_id]
    else:
        # Prioritize KA with lowest competency (gap targeting)
        ka_id, user_competency = min(competencies.items(), key=lambda x: x[1])

    # Determine target difficulty (match user level ±10%)
    target_difficulty_min = max(0.0, (user_competency / 100) - 0.10)
    target_difficulty_max = min(1.0, (user_competency / 100) + 0.10)

    # Get recent question history (last 7 days)
    recent_question_ids = db.get_recent_questions(user_id, days=7)

    # Build query
    eligible_questions = db.query(Question)\
        .filter(Question.ka_id == ka_id)\
        .filter(Question.difficulty.between(target_difficulty_min, target_difficulty_max))\
        .filter(Question.question_id.notin_(recent_question_ids))\
        .all()

    # Fallback: If no eligible questions (all answered recently), remove freshness constraint
    if not eligible_questions:
        eligible_questions = db.query(Question)\
            .filter(Question.ka_id == ka_id)\
            .filter(Question.difficulty.between(target_difficulty_min, target_difficulty_max))\
            .all()

    # Randomize to avoid predictable patterns
    import random
    selected_question = random.choice(eligible_questions)

    return selected_question
```

---

### Algorithm 5: SM-2 Spaced Repetition (Adapted)

**Purpose:** Schedule concept reviews at optimal intervals based on SuperMemo 2 algorithm, adapted for 60-day exam timeline.

**Trigger:** After user answers a review question

**Parameters:**
- `concept_tag`: Concept being reviewed
- `quality`: User's answer quality (0-5 scale, where 3+ = correct)
- `current_interval`: Current review interval in days
- `ease_factor`: Current ease factor (default: 2.5)

**Returns:** Next review date, updated interval, updated ease factor

**Standard SM-2 Intervals:** 1 day → 6 days → 6 * EF days → ...
**LearnR Adapted Intervals:** 1 day → 3 days → 7 days → 14 days (compressed for 60-day prep)

**Pseudocode:**
```python
def calculate_next_review_sm2_adapted(
    concept_tag: str,
    quality: int,  # 0-5 where 3+ = correct
    current_interval: int,
    ease_factor: float
) -> Tuple[date, int, float]:
    """
    Adapted SM-2 for 60-day exam prep timeline.

    Standard SM-2: 1d → 6d → 6*EF → (6*EF)*EF → ...
    LearnR Adapted: 1d → 3d → 7d → 14d (max)

    Rationale: 60 days insufficient for standard SM-2 long intervals
    """

    # Update ease factor based on answer quality
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)  # Minimum EF = 1.3

    # Determine next interval
    if quality < 3:
        # Incorrect: Reset to 1 day
        next_interval = 1
        ease_factor = max(1.3, ease_factor - 0.2)  # Penalize EF
    else:
        # Correct: Progress through intervals
        if current_interval == 0:  # First time
            next_interval = 1
        elif current_interval == 1:  # After 1 day
            next_interval = 3
        elif current_interval == 3:  # After 3 days
            next_interval = 7
        elif current_interval == 7:  # After 7 days
            next_interval = 14  # Max interval for 60-day prep
        else:
            next_interval = 14  # Cap at 14 days

    # Calculate next review date
    next_review_date = date.today() + timedelta(days=next_interval)

    return next_review_date, next_interval, ease_factor
```

---

### Algorithm 6: Reading Time Estimation

**Purpose:** Estimate reading time for BABOK content chunks

**Formula:** `estimated_minutes = word_count / 200`

**Rationale:** Average adult reading speed is 200-250 words per minute. We use 200 (conservative) to avoid underestimating.

**Pseudocode:**
```python
def estimate_reading_time(word_count: int) -> int:
    """Calculate estimated reading time in minutes."""
    WORDS_PER_MINUTE = 200
    estimated_minutes = word_count / WORDS_PER_MINUTE
    return max(1, round(estimated_minutes))  # Minimum 1 minute
```

**Examples:**
- 400-word chunk → 2 minutes
- 250-word chunk → 1 minute
- 600-word chunk → 3 minutes

---

## Epic Details

This section provides detailed user stories and acceptance criteria for each epic, following the sequence established in the Epic List. Each story is designed to deliver complete, testable functionality that can be implemented by a single developer in a focused 2-4 hour session.

---

### Epic 1: Foundation & User Authentication

**Epic Goal:** Establish the technical foundation for LearnR by setting up the monorepo structure, development environment, databases (PostgreSQL and Qdrant), and implementing secure user authentication. This epic delivers a working full-stack application with user registration, login, password management, and a health-check endpoint demonstrating end-to-end integration.

#### Story 1.1: Monorepo Setup and Project Scaffolding

As a **developer**,
I want to set up a monorepo with frontend and backend scaffolding,
so that the team has a consistent development environment and can begin building features immediately.

**Acceptance Criteria:**
1. Monorepo structure created with `/frontend`, `/backend`, `/shared`, `/scripts`, `/docs` directories
2. Frontend: React 18+ with TypeScript, Vite build tool, basic folder structure (`/src/components`, `/src/pages`, `/src/hooks`, `/src/utils`)
3. Backend: Python 3.11+ with FastAPI, basic folder structure (`/app/api`, `/app/models`, `/app/services`, `/app/utils`)
4. Package managers configured: npm/yarn for frontend, poetry/pip for backend
5. Environment variable management: `.env.example` files in both frontend and backend with required variables documented
6. README.md files in root and each directory explaining setup and development commands
7. Git repository initialized with `.gitignore` for Node, Python, environment files
8. Both frontend and backend can start locally (frontend on localhost:3000, backend on localhost:8000)

#### Story 1.2: PostgreSQL Database Setup and Schema Initialization

As a **backend developer**,
I want to set up PostgreSQL with initial schema and migrations,
so that user data and application state can be persisted reliably.

**Acceptance Criteria:**
1. PostgreSQL database created locally (development) with connection configuration
2. Alembic migrations configured for schema version control
3. Initial schema migration created with core tables:
   - `users` table (id, email, hashed_password, created_at, updated_at)
   - `onboarding_data` table (user_id FK, referral_source, certification, motivation, exam_date, knowledge_level, target_score, daily_study_time)
4. SQLAlchemy models created for `User` and `OnboardingData` with Pydantic schemas
5. Database connection pooling configured in FastAPI
6. Migration commands documented in README (`alembic upgrade head`, `alembic downgrade`, etc.)
7. Test database setup for running tests in isolation
8. All tables have appropriate indexes on foreign keys and frequently queried columns

#### Story 1.3: User Registration API

As a **user**,
I want to create an account with my email and password,
so that I can save my progress and access personalized learning features.

**Acceptance Criteria:**
1. POST `/api/auth/register` endpoint accepts `email` and `password` in request body
2. Email validation: Must be valid email format, unique in database (return 409 Conflict if duplicate)
3. Password validation: Minimum 8 characters, must contain at least one letter and one number
4. Password hashed using bcrypt or Argon2 before storage (never store plaintext)
5. User record created in `users` table with hashed password
6. Response returns user object (id, email, created_at) and JWT token with 7-day expiration
7. JWT token includes user_id in payload for authentication
8. Error responses: 400 Bad Request for validation errors, 409 Conflict for duplicate email, 500 Internal Server Error for database issues
9. Unit tests: Valid registration, duplicate email, weak password, invalid email format
10. Integration test: Full registration flow creates user in database and returns valid JWT

#### Story 1.4: User Login API

As a **registered user**,
I want to log in with my email and password,
so that I can access my personalized learning dashboard and progress.

**Acceptance Criteria:**
1. POST `/api/auth/login` endpoint accepts `email` and `password` in request body
2. User lookup by email (case-insensitive)
3. Password verification using bcrypt/Argon2 compare function
4. On successful authentication: Return JWT token (7-day expiration) and user object
5. On failed authentication: Return 401 Unauthorized with generic message "Invalid email or password" (no distinction to prevent enumeration)
6. JWT token structure same as registration (user_id in payload)
7. Rate limiting: Maximum 5 login attempts per email per 15 minutes (prevent brute force)
8. Unit tests: Valid login, invalid password, non-existent email, rate limiting
9. Integration test: Login returns valid JWT that can be used for authenticated endpoints
10. Security: No sensitive information in error messages, timing-safe password comparison

#### Story 1.5: Password Reset Flow

As a **user who forgot my password**,
I want to reset my password via email verification,
so that I can regain access to my account securely.

**Acceptance Criteria:**
1. POST `/api/auth/forgot-password` endpoint accepts `email`
2. Generate secure password reset token (UUID or similar, 1-hour expiration)
3. Store reset token in database with expiration timestamp (new `password_reset_tokens` table or add to `users`)
4. Send password reset email with reset link: `https://app.learnr.com/reset-password?token={token}`
5. Email sent even if email not found (prevent email enumeration, but no token created)
6. POST `/api/auth/reset-password` endpoint accepts `token` and `new_password`
7. Token validation: Exists, not expired, not already used
8. Password validation: Same rules as registration (8+ chars, letter + number)
9. Update user password (hash new password), invalidate reset token
10. Return success message (no JWT - user must log in with new password)
11. Unit tests: Valid reset, expired token, invalid token, weak new password
12. Integration test: Full password reset flow from forgot to login with new password

#### Story 1.6: JWT Authentication Middleware

As a **backend developer**,
I want JWT authentication middleware protecting authenticated endpoints,
so that only logged-in users can access protected resources.

**Acceptance Criteria:**
1. Middleware function `verify_jwt_token` that extracts JWT from `Authorization: Bearer {token}` header
2. Token validation: Signature valid, not expired, contains required `user_id` claim
3. On valid token: Attach `current_user` to request context (user_id, email)
4. On invalid/missing token: Return 401 Unauthorized with message "Authentication required"
5. Decorator `@require_auth` to protect routes (e.g., `@require_auth` above route handler)
6. Protected route example: GET `/api/user/profile` returns current user's profile
7. Unit tests: Valid token grants access, expired token denied, missing token denied, invalid signature denied
8. Integration test: Protected endpoint accessible with valid JWT, denied without JWT
9. Token refresh not implemented in MVP (7-day expiration sufficient)
10. Security: Token stored securely in frontend (HttpOnly cookie or secure localStorage, TBD by frontend)

#### Story 1.7: Health Check and API Documentation

As a **developer or DevOps engineer**,
I want a health check endpoint and auto-generated API documentation,
so that I can verify the backend is running and understand available endpoints.

**Acceptance Criteria:**
1. GET `/health` endpoint returns `200 OK` with JSON `{"status": "healthy", "timestamp": "ISO8601"}`
2. Health check verifies database connectivity (PostgreSQL ping)
3. FastAPI auto-generated OpenAPI documentation available at `/docs` (Swagger UI)
4. `/docs` shows all implemented endpoints with request/response schemas
5. `/redoc` alternative documentation format available
6. Health check does not require authentication (publicly accessible for monitoring)
7. API documentation shows authentication requirements (lock icon) for protected endpoints
8. Response examples included in API docs for each endpoint
9. Health check returns 503 Service Unavailable if database connection fails
10. README documents how to access API docs and health check endpoint

---

### Epic 2: Content Foundation & Question Bank

**Epic Goal:** Build the content processing pipeline to load, parse, embed, and serve all CBAP questions and BABOK v3 reading content. This epic delivers 600-1,000 questions with metadata, BABOK chunks with embeddings, Qdrant vector database setup, and functional content retrieval APIs that can be tested independently before integrating with user-facing features.

#### Story 2.1: Qdrant Vector Database Setup

As a **backend developer**,
I want to set up Qdrant locally via Docker and create collections for questions and reading content,
so that semantic search and content retrieval can function.

**Acceptance Criteria:**
1. Qdrant Docker container running locally (docker-compose.yml or standalone docker run command)
2. Qdrant accessible at `localhost:6333` with REST API and gRPC
3. Two collections created:
   - `cbap_questions`: Vector size 1536 (text-embedding-3-large), distance metric: Cosine
   - `babok_chunks`: Vector size 1536, distance metric: Cosine
4. Collection schemas include metadata fields (payload):
   - Questions: `question_id`, `ka`, `difficulty`, `concept_tags`, `question_text`, `options`, `correct_answer`
   - BABOK chunks: `chunk_id`, `ka`, `section_ref`, `difficulty`, `concept_tags`, `text_content`
5. Qdrant Python client installed and configured in backend
6. Connection test: Backend can create, read, update, delete (CRUD) vectors in both collections
7. Environment variable `QDRANT_URL` configurable (default: `http://localhost:6333`)
8. README documents Qdrant setup commands and how to verify collections exist
9. Qdrant data persisted to local volume (survives container restart)
10. Health check extended to verify Qdrant connectivity

#### Story 2.2: Vendor Question Import and Metadata Enrichment

As a **content manager**,
I want to import 500 vendor CBAP questions with metadata into PostgreSQL and Qdrant,
so that the platform has a high-quality question foundation.

**Acceptance Criteria:**
1. Questions table schema in PostgreSQL:
   - `questions` (id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, ka, difficulty, concept_tags JSONB, source VARCHAR, created_at)
2. Python script `/scripts/import_vendor_questions.py` reads vendor questions from CSV/JSON
3. Script validates each question: Required fields present, exactly 4 options, correct_answer is A/B/C/D, KA is one of 6 valid KAs
4. Difficulty labels assigned by expert or default to "Medium" if not provided
5. Concept tags extracted or manually assigned (JSONB array in PostgreSQL)
6. Questions inserted into PostgreSQL `questions` table (500 total)
7. Distribution validation: Each KA has at least 50 questions, balanced across difficulty levels
8. Script logs summary: Total questions imported, breakdown by KA and difficulty
9. Rollback mechanism if import fails mid-process (transaction-based insert or idempotent script)
10. README documents how to run import script and expected CSV/JSON format

#### Story 2.3: Question Embedding Generation and Qdrant Upload

As a **backend developer**,
I want to generate embeddings for all questions and upload to Qdrant,
so that semantic search can retrieve relevant questions.

**Acceptance Criteria:**
1. Python script `/scripts/generate_question_embeddings.py` reads all questions from PostgreSQL
2. For each question, create embedding text: `"{question_text} {option_a} {option_b} {option_c} {option_d}"`
3. Call OpenAI API `text-embedding-3-large` to generate 1536-dimension embedding vector
4. Batch API calls (up to 100 questions per request for efficiency)
5. Upload each question embedding to Qdrant `cbap_questions` collection with payload (question_id, ka, difficulty, concept_tags, question_text, options, correct_answer)
6. Script tracks progress (log every 50 questions embedded and uploaded)
7. Handle API rate limits: Retry with exponential backoff on 429 errors
8. Total embeddings: 500 vendor questions embedded
9. Verification: Query Qdrant collection, confirm 500 vectors exist
10. Script is idempotent (can re-run without duplicating embeddings, check if question_id already exists)

#### Story 2.4: BABOK v3 Parsing and Chunking

As a **content processor**,
I want to parse BABOK v3 PDF and chunk it into semantic segments,
so that targeted reading content can be retrieved for user gaps.

**Acceptance Criteria:**
1. Python script `/scripts/parse_babok.py` reads BABOK v3 PDF (path from environment variable or argument)
2. Extract text using PyMuPDF or pdfplumber (preserve structure: headings, paragraphs)
3. Identify 6 KA sections in BABOK (Business Analysis Planning, Elicitation, Requirements, Solution Evaluation, etc.)
4. Chunk text using hybrid strategy:
   - Structural chunking: Respect section/subsection boundaries (don't break mid-concept)
   - Semantic chunking: Target 200-500 tokens per chunk using LangChain RecursiveCharacterTextSplitter
5. Each chunk assigned metadata: KA, section_ref (e.g., "3.2.1 Stakeholder Analysis"), difficulty (Easy/Medium/Hard based on section complexity or default Medium), concept_tags (extracted keywords or manually assigned)
6. Chunks saved to PostgreSQL `babok_chunks` table (chunk_id, ka, section_ref, difficulty, concept_tags JSONB, text_content TEXT)
7. Validation: Total chunks approximately 200-500 (depends on BABOK length, aim for comprehensive coverage)
8. Distribution: Each KA has at least 20 chunks
9. Script logs summary: Total chunks created, breakdown by KA
10. README documents BABOK parsing script usage and expected output

#### Story 2.5: BABOK Chunk Embedding Generation and Qdrant Upload

As a **backend developer**,
I want to generate embeddings for all BABOK chunks and upload to Qdrant,
so that semantic retrieval can find relevant reading content for user gaps.

**Acceptance Criteria:**
1. Python script `/scripts/generate_babok_embeddings.py` reads all chunks from PostgreSQL `babok_chunks` table
2. For each chunk, use `text_content` as embedding input
3. Call OpenAI API `text-embedding-3-large` to generate 1536-dimension embedding
4. Batch API calls (up to 100 chunks per request)
5. Upload each chunk embedding to Qdrant `babok_chunks` collection with payload (chunk_id, ka, section_ref, difficulty, concept_tags, text_content)
6. Script tracks progress (log every 50 chunks embedded and uploaded)
7. Handle API rate limits: Retry with exponential backoff on 429 errors
8. Total embeddings: All BABOK chunks embedded (200-500 vectors)
9. Verification: Query Qdrant collection, confirm all chunks exist
10. Script is idempotent (check if chunk_id already exists before uploading)

#### Story 2.6: Content Retrieval API - Questions

As a **backend developer**,
I want an API endpoint to retrieve questions by filters (KA, difficulty, concept),
so that the quiz engine can select appropriate questions.

**Acceptance Criteria:**
1. GET `/api/content/questions` endpoint accepts query parameters: `ka`, `difficulty`, `concept_tags`, `limit` (default 10)
2. Query PostgreSQL `questions` table filtered by provided parameters
3. If `concept_tags` provided: Filter using JSONB containment (`concept_tags @> '{tag}'`)
4. Return JSON array of question objects (id, question_text, options, ka, difficulty, concept_tags, but NOT correct_answer or explanation - those come after answer submission)
5. Response includes pagination metadata: `total_count`, `page`, `limit`
6. Endpoint requires authentication (`@require_auth` middleware)
7. Unit tests: Filter by KA, filter by difficulty, filter by concept_tags, no filters (returns all up to limit)
8. Integration test: API returns questions matching filters
9. Performance: Query executes in <100ms for up to 1000 questions
10. API documentation updated in `/docs` with parameter descriptions and example responses

#### Story 2.7: Content Retrieval API - BABOK Chunks

As a **backend developer**,
I want an API endpoint to retrieve BABOK chunks via semantic search,
so that targeted reading content can be presented to users.

**Acceptance Criteria:**
1. POST `/api/content/reading` endpoint accepts JSON body: `query_text` (user's knowledge gap description), `ka` (optional filter), `limit` (default 3)
2. Generate embedding for `query_text` using OpenAI `text-embedding-3-large`
3. Query Qdrant `babok_chunks` collection with vector search (cosine similarity)
4. Apply filters: If `ka` provided, filter results to that KA only
5. Return top `limit` chunks ranked by similarity score
6. Response: JSON array of chunk objects (chunk_id, ka, section_ref, text_content, similarity_score)
7. Endpoint requires authentication
8. Unit tests: Search returns relevant chunks, KA filter works, limit parameter works
9. Integration test: Semantic search finds BABOK content related to query (e.g., "stakeholder analysis" retrieves relevant section)
10. Performance: Vector search executes in <500ms including embedding generation

---

### Epic 3: Diagnostic Assessment & Competency Baseline

**Epic Goal:** Enable first-time users to complete the anonymous 7-question onboarding flow (starting with first question inline on landing page), create an account, take the 12-question diagnostic assessment, and receive accurate baseline competency scores across all 6 CBAP knowledge areas with gap analysis and recommendations.

#### Story 3.1: Landing Page with Inline First Onboarding Question

As a **first-time visitor**,
I want to see the value proposition and immediately engage with the first onboarding question on the landing page,
so that I can start my learning journey with minimal friction.

**Acceptance Criteria:**
1. Landing page displays LearnR value proposition (headline, subheadline, key benefits - trust, adaptive learning, reading content, spaced repetition)
2. First onboarding question displayed **inline immediately below value prop** (no "Sign Up" button friction): "How did you hear about LearnR?" with options (Search, Referral, Social Media, Other)
3. User selects answer → automatically progresses to Question 2 in same container (no separate "Submit" button, no page reload - smooth fade-in/slide transition 300ms)
4. Question 1 answer stored in browser sessionStorage (no server call yet, user not authenticated)
5. Visual design: Framer-inspired aesthetic, Inter font, pill-rounded answer buttons (border-radius: 9999px), primary information card styling (22px border radius)
6. Progress indicator: "Question 1 of 7" displayed
7. Page is mobile-responsive (works on 375px width minimum)
8. Loading state: Page renders in <3 seconds on 3G connection
9. Accessibility: Keyboard navigation works (tab to options, enter to select), screen reader announces question and options
10. Unit tests: Question renders, selection progresses to next question, sessionStorage updated

#### Story 3.2: Onboarding Questions 2-7 (Progressive Disclosure)

As a **user progressing through onboarding**,
I want to answer questions 2-7 sequentially in the same container,
so that the platform learns my context and can personalize my learning experience.

**Acceptance Criteria:**
1. **Questions 2-7 appear sequentially in same container as Q1** (progressive disclosure, not separate pages)
   - Smooth fade-in/slide animation (300ms) between questions
   - No page reload, all client-side transitions
   - Previous answers stored in sessionStorage immediately
2. Question 2: "Which certification are you preparing for?" → Options: CBAP (default for MVP), [Other certifications grayed out/disabled]
3. Question 3: "What's your primary motivation?" → Options: Career advancement, Salary increase, Credibility, Personal growth, Other
4. Question 4: "When is your exam scheduled?" → Date picker (minimum: today + 30 days, maximum: today + 365 days), displays "X days until exam" after selection
5. Question 5: "What's your current knowledge level?" → Options: Beginner (new to BA), Intermediate (some experience), Advanced (experienced BA, need exam prep)
6. Question 6: "What's your target competency score?" → Options: 70% (pass threshold), 80% (confident pass), 90% (mastery)
7. Question 7: "How much time can you commit daily?" → Options: 30-60 minutes, 1-2 hours, 2+ hours
8. Each answer stored in sessionStorage immediately upon selection
9. **SessionStorage schema:** See `/docs/front-end-spec.md` Lines 391-407 for exact data structure:
   ```javascript
   {
     "onboarding_answers": {
       "referral_source": "search",
       "exam_type": "CBAP",
       "motivation": "career_advancement",
       "exam_date": "2025-12-21",
       "knowledge_level": "intermediate",
       "target_score": "pass",
       "daily_commitment": "1hr"
     },
     "started_at": "ISO8601 timestamp",
     "current_question": 7
   }
   ```
10. Progress indicator updates: "Question 2 of 7", "Question 3 of 7", etc. (thin progress bar at top of screen)
11. Optional "← Back" button allows returning to previous question (except from Q1 to landing page)
12. After Question 7 answered → automatically transition to Account Creation screen (same container, slide transition)

#### Story 3.3: Account Creation After Onboarding

As a **user who completed 7 onboarding questions**,
I want to create an account to save my progress,
so that I can proceed to the diagnostic assessment and access my personalized learning.

**Acceptance Criteria:**
1. Account creation screen displays message: "Create your account to save your progress and start your diagnostic assessment"
2. Form fields: Email (required, validated), Password (required, 8+ chars, letter + number), Confirm Password (must match)
3. Visual summary of onboarding data displayed above form (exam date: "X days until exam", target: Y%, daily time: Z hours) - builds trust that data is captured
4. "Create Account" button (pill-rounded, primary color)
5. On submit: POST to `/api/auth/register` with email + password
6. On successful registration: Receive JWT token, store in localStorage or HttpOnly cookie
7. Immediately POST onboarding data to `/api/user/onboarding` (7 answers persisted to user profile)
8. Clear sessionStorage after successful account creation (data now in database)
9. Redirect to Diagnostic Assessment screen
10. Error handling: Display validation errors inline (email already exists → "Email already registered, please login"), weak password → "Password must be at least 8 characters with letter and number"
11. "Already have an account? Login" link navigates to login page (edge case: returning user who started onboarding)

#### Story 3.4: Diagnostic Assessment Question Selection

As a **backend developer**,
I want to select 12 balanced diagnostic questions (3 per KA) with varied difficulty,
so that the diagnostic provides accurate baseline competency assessment.

**Acceptance Criteria:**
1. GET `/api/diagnostic/questions` endpoint (requires authentication)
2. Select exactly 12 questions: 3 from each of 6 KAs
3. Difficulty distribution per KA: 1 Easy, 1 Medium, 1 Hard (balanced assessment)
4. Questions selected randomly from available pool (different diagnostic each time, prevents memorization if retaken)
5. Question order randomized (not clustered by KA - intermix to reduce pattern recognition)
6. Response: JSON array of 12 question objects (id, question_text, options [A, B, C, D], ka, difficulty) - NO correct_answer or explanation yet
7. Mark diagnostic session as "in_progress" in database (track user's diagnostic state)
8. Unit tests: 12 questions returned, 3 per KA, varied difficulty, randomized order
9. Integration test: API returns valid diagnostic questions for authenticated user
10. Performance: Question selection in <500ms

#### Story 3.5: Diagnostic Assessment UI and Answer Recording

As a **user taking the diagnostic**,
I want to answer 12 questions in a focused, distraction-free interface,
so that I can provide accurate responses reflecting my true knowledge level.

**Acceptance Criteria:**
1. Diagnostic screen displays one question at a time (full-screen or centered, minimal chrome)
2. Question display: Question text, 4 options (A/B/C/D as pill-rounded buttons), progress "Question X of 12"
3. User selects one option → "Submit Answer" button enabled (or auto-advance on selection, UX decision TBD)
4. On submit: POST `/api/diagnostic/answer` with `question_id` and `selected_answer`
5. No immediate feedback (correct/incorrect not shown during diagnostic - per requirements)
6. Auto-advance to next question after answer recorded
7. Answers stored in `diagnostic_responses` table (user_id, question_id, selected_answer, timestamp)
8. After 12th question submitted → automatically calculate competency scores (Story 3.6)
9. Visual design: Focused mode, Inter font, pill buttons, secondary card styling for question container (14px radius)
10. No "Back" button during diagnostic (prevents changing answers after seeing later questions)
11. Session timeout warning at 30 minutes (if user pauses mid-diagnostic)

#### Story 3.6: Baseline Competency Calculation (Simplified IRT)

As a **system**,
I want to calculate baseline competency scores for each KA using simplified Item Response Theory,
so that users receive accurate assessment of their current knowledge level.

**Acceptance Criteria:**
1. After 12th diagnostic answer submitted, trigger competency calculation
2. For each KA, calculate competency score based on 3 questions answered:
   - Simplified IRT: Correct answer on Hard question → higher competency increase than Easy
   - Scoring formula (simplified): Base score 50%, +15% per correct Easy, +20% per correct Medium, +25% per correct Hard
   - Example: 1 correct Easy + 1 correct Medium + 0 correct Hard = 50% + 15% + 20% = 85% competency
3. Store competency scores in `competency_tracking` table (user_id, ka, competency_score, last_updated)
4. Calculate overall exam readiness score (average of 6 KA scores or weighted by CBAP exam distribution if data available)
5. Identify gap areas: KAs with competency < 70% flagged as "needs focus"
6. Unit tests: Various answer combinations produce expected competency scores, all 6 KAs have scores calculated
7. Integration test: Full diagnostic flow calculates and stores competency scores
8. Performance: Calculation executes in <1 second
9. Algorithm documented in `/docs/algorithms.md` for future refinement
10. Initial calibration: Expert review validates that competency scores feel accurate (e.g., 3/3 correct Hard questions → ~95-100% competency)

#### Story 3.7: Diagnostic Results Screen with Gap Analysis

As a **user who completed the diagnostic**,
I want to see my baseline competency scores and understand which areas need focus,
so that I can start studying effectively with clear direction.

**Acceptance Criteria:**
1. Results screen displays after diagnostic completion (GET `/api/diagnostic/results`)
2. Hero metric: Exam Readiness Score (0-100%, large display, color-coded: Red <70%, Orange 70-85%, Green >85%)
3. Six KA competency bars visualized (horizontal bars or radial chart, showing score 0-100% for each KA)
4. Each KA bar color-coded: Red (<70%), Orange (70-85%), Green (>85%)
5. Gap analysis section: "Focus Areas" listing KAs with <70% competency, sorted by lowest score first
6. Recommendations: "Start with [Lowest KA Name] where you scored X%"
7. Days until exam displayed: "X days to prepare"
8. Primary CTA: "Start Learning" button (pill-rounded, primary color) → navigates to first adaptive quiz session
9. Secondary CTA: "Retake Diagnostic" (if user wants to reset baseline - confirmation modal warns this will reset all competency tracking)
10. Visual design: Main screen container (35px radius), competency cards (22px radius), Framer-inspired layout, Inter font
11. Accessibility: Screen reader announces competency scores, color-coding supplemented with text labels (not color-only)
12. Post-diagnostic survey: "How accurately did this assessment reflect your knowledge?" (5-point scale: Very Inaccurate to Very Accurate) → target 80%+ "Accurate" or "Very Accurate"

---

### Epic 4: Adaptive Quiz Engine & Explanations

**Epic Goal:** Implement the core adaptive learning loop where users answer questions selected intelligently based on their competency gaps and difficulty matching, receive immediate feedback, and read detailed explanations for every question. This epic delivers quiz session management, real-time competency updates, and user feedback mechanisms.

**User Flow Reference:** See `docs/user-flows.md` Flow #4 (Learning Loop) and Flow #4b (Post-Session Review Flow) for visual representation of the complete learning experience including the post-session review phase introduced in v2.1.

#### Story 4.1: Quiz Session Creation and Management

As a **user ready to study**,
I want to start an adaptive quiz session,
so that I can practice questions matched to my competency level and knowledge gaps.

**Acceptance Criteria:**
1. POST `/api/quiz/session/start` endpoint creates new quiz session (requires authentication)
2. Session metadata stored: session_id, user_id, start_time, session_type ("new_content" for now, "mixed" added in Epic 7)
3. Session state tracked: questions_answered_count, current_question_id, is_paused, is_completed
4. Response: session_id and first adaptive question selected (Story 4.2 logic)
5. User can have only one active session at a time (if existing session incomplete → return existing session_id)
6. GET `/api/quiz/session/{session_id}` retrieves session state (questions answered so far, current question)
7. POST `/api/quiz/session/{session_id}/pause` pauses session (save state, can resume later)
8. POST `/api/quiz/session/{session_id}/end` ends session (mark completed, save end_time, calculate session stats)
9. Sessions auto-expire after 2 hours of inactivity (background cleanup job)
10. Unit tests: Session creation, pause, resume, end, retrieve state

#### Story 4.2: Adaptive Question Selection Logic

As a **quiz engine**,
I want to select the next question adaptively based on user's competency, knowledge gaps, and difficulty matching,
so that every question maximizes learning efficiency.

**Acceptance Criteria:**
1. Algorithm (`/app/services/adaptive_selection.py`):
   - **Step 1:** Identify weakest 2-3 KAs (lowest competency scores)
   - **Step 2:** Prioritize questions from weakest KAs (60% probability) vs. all KAs for breadth (40% probability)
   - **Step 3:** Match difficulty to user's current competency in that KA: <70% → Easy/Medium, 70-85% → Medium/Hard, >85% → Hard
   - **Step 4:** Filter out recently seen questions (exclude questions answered in last 7 days)
   - **Step 5:** Randomly select one question from filtered pool
2. Within-session difficulty adjustment (per Epic template requirements):
   - Track consecutive correct/incorrect answers in same KA within current session
   - If 3+ consecutive correct in KA → increase difficulty for next question in that KA (e.g., Medium → Hard)
   - If 3+ consecutive incorrect in KA → decrease difficulty for next question in that KA (e.g., Hard → Medium)
   - Adjustment resets between sessions (competency tracking persists, but within-session streaks don't)
3. Question returned includes: question_id, question_text, options, ka, difficulty (NO correct_answer or explanation yet)
4. Log selection rationale (for debugging): KA chosen, difficulty rationale, streak adjustment applied (if any)
5. Unit tests: Weakest KA prioritized, difficulty matched to competency, recently seen questions excluded, consecutive performance adjusts difficulty
6. Integration test: Adaptive selection returns appropriate questions across multiple quiz sessions
7. Performance: Selection logic executes in <200ms
8. Algorithm refinement: Monitor user feedback ("too easy" / "too hard") for future calibration

#### Story 4.3: Answer Submission and Immediate Feedback

As a **user answering a quiz question**,
I want to submit my answer and immediately see if I was correct or incorrect,
so that I receive instant feedback on my understanding.

**Acceptance Criteria:**
1. POST `/api/quiz/answer` endpoint accepts: session_id, question_id, selected_answer (A/B/C/D)
2. Record response in `quiz_responses` table (user_id, session_id, question_id, selected_answer, is_correct, time_taken, timestamp)
3. Determine correctness: Compare `selected_answer` to question's `correct_answer`
4. Response JSON:
   - `is_correct`: true/false
   - `correct_answer`: The right answer (e.g., "B")
   - `explanation`: Detailed explanation text
   - `competency_update`: New competency score for this KA (see Story 4.4)
5. Frontend displays immediate visual feedback:
   - Correct answer: Green checkmark icon, "Correct!" message
   - Incorrect answer: Orange/red X icon, "Incorrect. The correct answer is B."
6. No auto-advance yet (user must click "Next" after reading explanation - Story 4.5)
7. Track time_taken (client-side or server-side timestamp diff from question displayed to answer submitted)
8. Unit tests: Correct answer recorded, incorrect answer recorded, response includes explanation
9. Integration test: Full answer submission flow updates database and returns feedback
10. Error handling: Invalid session_id or question_id → 400 Bad Request

#### Story 4.4: Real-Time Competency Score Updates

As a **system**,
I want to update the user's competency score for the relevant KA after every quiz answer,
so that competency tracking reflects current knowledge level in real-time.

**Acceptance Criteria:**
1. After answer submission (Story 4.3), trigger competency update for the question's KA
2. Simplified IRT update logic:
   - Correct answer on Hard question: +5% competency (or more sophisticated IRT calculation)
   - Correct answer on Medium: +3% competency
   - Correct answer on Easy: +2% competency
   - Incorrect answer: -1% competency (small penalty to reflect gap)
   - Competency score capped at 0-100%
3. Update `competency_tracking` table: Set new `competency_score`, update `last_updated` timestamp
4. Include updated competency score in answer submission response (Story 4.3)
5. Exam readiness score recalculated as average (or weighted average) of all 6 KA scores
6. Unit tests: Various answer/difficulty combinations produce expected competency changes, score stays within 0-100%
7. Integration test: Multiple answers update competency progressively
8. Performance: Competency update executes in <100ms (included in answer submission response time)
9. Algorithm documented in `/docs/algorithms.md` for future refinement (full IRT in Phase 2)
10. Historical competency tracking: Store snapshots weekly for progress trends (see Epic 6)

#### Story 4.5: Explanation Display with User Feedback

As a **user who answered a question**,
I want to read a detailed explanation of why the correct answer is right and why other options are wrong,
so that I learn the concept rather than just memorizing answers.

**Acceptance Criteria:**
1. After answer submission and immediate feedback (Story 4.3), display explanation section below result
2. Explanation text retrieved from question's `explanation` field (loaded during question import, Story 2.2)
3. Explanation formatting:
   - **Maximum 200 characters total** (enforced during content creation) - concise, focused explanations
   - **"Why [Correct Answer] is correct:"** section explaining the right answer (2-3 sentences maximum)
   - **"Why other options are incorrect:"** brief explanation for each wrong option
   - **BABOK reference:** "See BABOK v3 Section X.Y.Z for more details" (included within 200-char limit if applicable)
   - **Rationale:** 200-char limit ensures explanations fit on screen without scrolling, reducing cognitive load
4. Explanation card styled with secondary card border radius (14px), readable typography (Inter font, adequate line spacing)
5. User feedback mechanism: Thumbs up / thumbs down icons below explanation
   - Click thumbs up → POST `/api/feedback/explanation` with `question_id`, `helpful: true`
   - Click thumbs down → POST `/api/feedback/explanation` with `question_id`, `helpful: false`
   - Feedback stored in `explanation_feedback` table (user_id, question_id, helpful, timestamp)
   - Visual feedback: Icon highlights after click, "Thanks for your feedback!" message
6. "Report Issue" link allows flagging incorrect questions (POST `/api/feedback/report` with `question_id`, `issue_description`)
7. "Next Question" button (pill-rounded, primary color) below explanation → advances to next adaptive question (Story 4.2 selects next)
8. Accessibility: Explanation text is screen-reader friendly, thumbs icons have alt text
9. Unit tests: Explanation renders, feedback submission works
10. Integration test: User can read explanation and provide feedback after answering question

#### Story 4.6: Post-Session Review Initiation (v2.1 NEW)

As a **user who completed a quiz session with incorrect answers**,
I want to immediately review all questions I got wrong,
so that I can reinforce correct understanding and improve retention.

**Acceptance Criteria:**
1. When quiz session ends (user clicks "End Session"), backend checks for incorrect answers in this session
2. If incorrect answers exist → redirect to Post-Session Review Transition Screen instead of dashboard
3. If all answers correct (perfect score) → show congratulatory message, skip review, return to dashboard
4. Transition screen displays:
   - Header: "Great work! Let's review X questions you got wrong"
   - Subtext: "Immediate review improves retention 2-3x"
   - Primary CTA: "Start Review" (pill-rounded button)
   - Secondary CTA: "Skip Review" (text link, less prominent)
5. POST `/api/v1/sessions/{session_id}/review/start` creates `session_reviews` record with status `not_started`
6. Response includes review_id, total_questions_to_review, and array of incorrect question IDs
7. If user clicks "Skip Review" → show confirmation modal: "Are you sure? Reviewing now will strengthen retention"
8. If user confirms skip → POST `/api/v1/sessions/{session_id}/review/skip`, update review status to `skipped`, return to dashboard
9. Track review skip rate for analytics (target: <30% skip rate)
10. Unit tests: Review initiation triggered only when incorrect answers exist
11. Integration test: User completing session with incorrect answers sees review transition screen

#### Story 4.7: Re-Present Incorrect Questions for Review

As a **user in review mode**,
I want to re-answer each question I got wrong,
so that I can test my understanding and reinforce the correct answer.

**Acceptance Criteria:**
1. Review screen displays first incorrect question with "REVIEW" badge (distinct visual indicator)
2. Progress indicator: "Review Question 1 of X" (shows current position in review)
3. Question display identical to quiz session (same format, same 4 options)
4. User cannot see their original incorrect answer (clean slate for re-attempt)
5. User selects answer and clicks "Submit Answer"
6. POST `/api/v1/sessions/{session_id}/review/answer` with:
   - `original_attempt_id` (FK to original incorrect attempt)
   - `selected_choice_id` (user's new answer)
   - `time_spent_seconds`
7. Backend creates `review_attempts` record linking to `session_reviews` and `question_attempts`
8. Backend calculates `is_correct` (boolean) and `is_reinforced` (true if incorrect → correct)
9. Response returns: `is_correct`, `is_reinforced`, `correct_answer`, `explanation`
10. Frontend displays immediate feedback:
    - If reinforced (incorrect → correct): Green checkmark + "Great improvement! 🎉"
    - If still incorrect: Orange X + "Still incorrect. Correct answer is: B"
11. Update competency score based on review performance (reinforced = +2% boost, still incorrect = neutral)
12. Automatically advance to next review question or review summary if complete
13. Unit tests: Review attempt recorded correctly, reinforcement logic works
14. Integration test: User can re-answer all incorrect questions and see appropriate feedback

#### Story 4.8: Review Performance Tracking and Summary

As a **user who completed post-session review**,
I want to see a summary of my review performance,
so that I can understand my improvement and identify concepts needing more practice.

**Acceptance Criteria:**
1. After last review question answered → display Review Summary Screen
2. Summary displays:
   - Total questions reviewed: X
   - Reinforced correctly (incorrect → correct): Y (green)
   - Still incorrect: Z (orange)
   - Improvement calculation: "Original: 80% → Final: 93% (+13%)"
3. "Original" score = session accuracy BEFORE review (e.g., 12/15 = 80%)
4. "Final" score = session accuracy AFTER review (e.g., 14/15 = 93%, assuming 2 reinforced)
5. Display list of still-incorrect questions with:
   - Question preview (first 50 chars)
   - Knowledge Area tag
   - "These will appear in spaced repetition reviews"
6. POST `/api/v1/sessions/{session_id}/review/complete` updates `session_reviews`:
   - `review_status` = `completed`
   - `questions_reinforced_correctly` = count
   - `questions_still_incorrect` = count
   - `review_completed_at` = timestamp
7. Primary CTA: "Return to Dashboard" → updates dashboard with new competency scores
8. Track review completion rate (target: 70%+ of users complete review when prompted)
9. Track reinforcement success rate (target: 60%+ of review attempts are reinforced)
10. Unit tests: Summary calculations accurate, metrics tracked correctly
11. Integration test: Completed review updates session_reviews table and returns user to dashboard

#### Story 4.9: Review Analytics and Dashboard Integration

As a **system**,
I want to track post-session review engagement and performance metrics,
so that we can validate the 2-3x retention improvement hypothesis and measure feature adoption.

**Acceptance Criteria:**
1. Dashboard displays review completion metrics:
   - Total reviews completed
   - Average reinforcement success rate (% of incorrect → correct)
   - Review adoption rate (% of sessions with reviews that user completed)
2. Analytics track per-user:
   - `total_reviews_offered` (sessions with incorrect answers)
   - `total_reviews_completed`
   - `total_reviews_skipped`
   - `total_questions_reinforced`
3. GET `/api/dashboard` response includes:
   - `review_stats.adoption_rate` (float, 0.0-1.0)
   - `review_stats.reinforcement_success_rate` (float, 0.0-1.0)
   - `review_stats.total_reinforced` (int)
4. Admin endpoint GET `/api/admin/alpha-metrics` includes:
   - Platform-wide review adoption rate
   - Platform-wide reinforcement success rate
   - User cohort comparison (reviewers vs. non-reviewers retention rates)
5. Spaced repetition algorithm prioritizes still-incorrect questions from reviews (schedule for +1 day review)
6. Correctly reinforced questions get standard spaced repetition interval (+3 days)
7. Track reading time during review phase (if user expands explanations or reading materials)
8. **Analytics Event Logging:** All review interactions must emit standardized events for tracking:
   - **Event: `post_session_review_started`** - Emitted when user begins review
     - Fields: `session_id`, `user_id`, `total_questions_to_review`, `original_session_accuracy`, `timestamp`
   - **Event: `review_question_answered`** - Emitted after each review answer submitted
     - Fields: `review_id`, `question_id`, `original_answer`, `review_answer`, `is_reinforced`, `time_spent_seconds`, `timestamp`
   - **Event: `review_reading_expanded`** - Emitted when user expands reading material during review
     - Fields: `review_id`, `chunk_id`, `question_id`, `babok_section`, `time_spent_seconds`, `timestamp`
   - **Event: `post_session_review_completed`** - Emitted when review phase finishes
     - Fields: `review_id`, `session_id`, `total_reviewed`, `reinforced_correctly`, `still_incorrect`, `reading_chunks_viewed`, `total_reading_time_seconds`, `final_accuracy`, `accuracy_improvement`, `timestamp`
   - **Event: `post_session_review_skipped`** - Emitted when user skips review
     - Fields: `session_id`, `questions_to_review`, `original_accuracy`, `timestamp`
9. Unit tests: Analytics calculations accurate, all events logged correctly with proper schemas
10. Integration test: Review completion updates user analytics and dashboard metrics, events are emitted
11. Performance: Dashboard analytics queries optimized with database indexes on `session_reviews(user_id, review_status)`

---

### Epic 5: Targeted Reading Content Integration

**🚨 CRITICAL IMPLEMENTATION NOTE - v2.1 Update:**

**Stories 5.1-5.4 are DEPRECATED.** They describe the v2.0 synchronous reading model (inline reading after explanations) which was found to interrupt learning flow and reduce engagement. These stories are preserved **for historical reference only**.

**Stories 5.5-5.9 are the AUTHORITATIVE implementation.** LearnR v2.1 implements the **Asynchronous Reading Library** model which provides superior UX through:
- Zero interruption to learning flow ("test fast, read later")
- User control over when to engage with reading materials
- Prioritized reading queue with smart filtering
- 2x improvement in reading engagement (25% → 50%+ expected)

**For software architects:** Implement Stories 5.5-5.9 (Async Reading Library). Do NOT implement Stories 5.1-5.4 unless explicitly directed for a specific integration scenario.

**Detailed Specifications:** See `/docs/Asynchronous_Reading_Model.md` for complete technical architecture of the v2.1 async reading system.

**User Flow Reference:** See `docs/user-flows.md` Flow #9 (Reading Library Flow) for visual representation of the asynchronous reading queue system introduced in v2.1. This flow shows how users access curated reading materials on-demand without interrupting their quiz experience.

**Epic Goal:** Complete the learning loop by adding semantic retrieval of BABOK v3 reading content that addresses user-specific knowledge gaps. This is the **critical differentiator** for LearnR - transforming it from "just another quiz app" to a complete learning system. This epic delivers vector search, reading content display after explanations, and engagement tracking to validate the differentiation value during Day 24 alpha test.

#### Story 5.1: Gap-Based Reading Content Retrieval

As a **system**,
I want to automatically retrieve relevant BABOK reading chunks after a user answers a question incorrectly,
so that users can read targeted content addressing their specific knowledge gaps.

**Acceptance Criteria:**
1. After answer submission (Story 4.3), if answer is **incorrect** → trigger reading content retrieval
2. Generate query for semantic search:
   - Primary: Question's `concept_tags` (e.g., ["stakeholder analysis", "requirements elicitation"])
   - Secondary: Question text itself (if concept_tags not comprehensive)
3. Call `/api/content/reading` (Story 2.7) with query_text and KA filter (same KA as question)
4. Retrieve top 2-3 BABOK chunks ranked by semantic similarity
5. Filter chunks by difficulty: Match to user's competency level in this KA (e.g., if user at 60% competency, retrieve Easy/Medium chunks, not Hard)
6. Return chunks in response to answer submission (Story 4.3 response expanded to include `reading_content` array)
7. If answer is **correct** on Easy/Medium question → no reading content (user already knows this, don't overwhelm)
8. If answer is **correct** on Hard question → optionally show 1 chunk for reinforcement (configurable)
9. Unit tests: Incorrect answer triggers retrieval, correct Easy answer does not, KA filtering works
10. Integration test: Semantic search returns BABOK content relevant to missed question concept

#### Story 5.2: Reading Content Display in Quiz Flow

As a **user who answered incorrectly**,
I want to read relevant BABOK content immediately after seeing the explanation,
so that I can understand the concept more deeply and fill my knowledge gap.

**Acceptance Criteria:**
1. Reading content section displays after explanation (Story 4.5), before "Next Question" button
2. Section header: "Learn More: Targeted Reading from BABOK v3" (clarifies source and purpose)
3. Display 2-3 reading chunks as expandable cards (14px border radius, secondary styling)
4. Each chunk card shows:
   - **BABOK Section Reference:** "Section 3.2.1: Stakeholder Analysis"
   - **Preview:** First 100 characters of `text_content` + "... Read more"
   - **Expand/Collapse:** Click to show full text_content (200-500 tokens)
5. Expanded state: Full text displayed with readable formatting (line spacing, paragraph breaks preserved)
6. "Mark as Read" checkbox for each chunk (tracks engagement)
7. If user clicks "Mark as Read" → POST `/api/reading/track` with `chunk_id`, stores in `reading_history` table (user_id, chunk_id, marked_read: true, timestamp)
8. "Skip Reading" button allows advancing to next question without reading (optional, not forced)
9. Visual design: Reading section visually separated from explanation (subtle border or background color), Inter font, adequate spacing
10. Accessibility: Expandable sections keyboard-accessible (Enter to expand/collapse), screen reader announces expanded state

#### Story 5.3: Reading Engagement Tracking and Analytics

As a **product manager**,
I want to track which reading chunks users engage with and how long they spend reading,
so that I can validate the reading feature's value during alpha test (Day 24 Go/No-Go decision).

**Acceptance Criteria:**
1. Track reading engagement events in `reading_engagement` table (user_id, chunk_id, session_id, displayed_at, expanded_at, time_spent_seconds, marked_read)
2. Frontend JavaScript tracks:
   - **Displayed:** Chunk shown to user (logged immediately)
   - **Expanded:** User clicked to read full content (logged on expand)
   - **Time Spent:** Seconds from expand to next action (collapse, next question, etc.) - measure reading duration
   - **Marked Read:** User clicked "Mark as Read" checkbox
3. POST `/api/reading/engagement` endpoint accepts engagement events from frontend
4. Engagement metrics calculated per user:
   - **Reading Engagement Rate:** % of displayed chunks that were expanded (target 60%+ per requirements)
   - **Average Time Spent:** Seconds per chunk (target 2-4 minutes for 200-500 token chunks per Brief)
   - **Marked Read Rate:** % of expanded chunks marked as read
5. Dashboard for product team (not user-facing): Aggregate reading metrics across all users
   - Total chunks displayed vs. expanded vs. marked read
   - Average engagement rate and time spent
   - Breakdown by KA (which KAs have highest reading engagement)
6. Alpha test validation (Day 24): Check if engagement rate >60% and user feedback positive (Story 5.4)
7. Unit tests: Engagement events logged correctly, metrics calculated accurately
8. Integration test: Full quiz flow logs reading engagement from display to mark-as-read
9. Performance: Engagement logging does not slow down quiz flow (<100ms latency)
10. Privacy: Engagement data anonymized for aggregate analytics

#### Story 5.4: Reading Content Feedback and Relevance Validation

As a **user reading BABOK content**,
I want to provide feedback on whether the content was relevant to my knowledge gap,
so that the platform can improve content retrieval accuracy.

**Acceptance Criteria:**
1. Below each reading chunk, display feedback prompt: "Was this content relevant to your gap?" with Thumbs Up / Thumbs Down icons
2. Click thumbs up → POST `/api/feedback/reading` with `chunk_id`, `relevant: true`
3. Click thumbs down → POST `/api/feedback/reading` with `chunk_id`, `relevant: false`, optional `reason` text field (e.g., "Too basic", "Not related to question", "Too advanced")
4. Feedback stored in `reading_feedback` table (user_id, chunk_id, relevant, reason, timestamp)
5. Visual feedback: Icon highlights after click, "Thanks for your feedback!" message
6. Relevance metrics calculated:
   - **Relevance Rate:** % of chunks rated thumbs up (target 80%+ per Brief requirements)
   - Breakdown by KA and difficulty level
7. Product team dashboard shows relevance metrics to validate semantic search quality
8. Alpha test validation (Day 24): Check if relevance rate >70% (acceptable) or >80% (excellent) to determine Go/No-Go for reading feature
9. Unit tests: Feedback submission works, relevance metrics calculated
10. Integration test: User can rate reading content relevance, data persists

#### Story 5.5: Background Reading Queue Population (v2.1 NEW - ASYNC MODEL)

As a **system**,
I want to automatically add relevant reading materials to the user's reading queue as they answer questions,
so that users have curated study materials available without interrupting their quiz flow.

**Acceptance Criteria:**
1. After user answers ANY question (correct or incorrect), trigger async background process to add reading materials
2. For incorrect answers: Add 2-3 high-priority BABOK chunks (semantic search on question concepts + KA)
3. For correct answers on Hard questions: Add 1 medium-priority chunk for reinforcement (optional, configurable)
4. For correct answers on Easy/Medium: Skip reading recommendation (user already understands)
5. Semantic search query composition:
   - Primary: Question `concept_tags` (e.g., ["stakeholder analysis", "requirements elicitation"])
   - Secondary: Question text if concept_tags insufficient
   - Filter: Same KA as question
6. POST `/api/v1/reading/queue` (internal/background call) with:
   - `user_id`, `chunk_id`, `question_id`, `session_id`
   - `was_incorrect` (boolean), `relevance_score` (from semantic search), `ka_id`
   - `priority` calculated based on: competency gap in KA (larger gap = higher priority), question difficulty
7. Priority calculation logic:
   - High: User competency in KA <60% AND incorrect answer
   - Medium: User competency 60-80% OR correct on hard question
   - Low: User competency >80% AND correct answer (rare, for completeness)
8. Database: Insert into `reading_queue` table with `reading_status = 'unread'`
9. Duplicate prevention: If chunk already in user's queue → update `relevance_score` if higher, don't duplicate
10. Performance: Background process <200ms, doesn't block answer submission response
11. Unit tests: Reading queue population triggered correctly, priority calculation accurate
12. Integration test: Answering questions adds appropriate reading materials to queue

#### Story 5.6: Silent Badge Updates in Navigation

As a **system**,
I want to update the reading library badge count silently as new materials are added,
so that users are aware of new content without interrupting their quiz flow.

**Acceptance Criteria:**
1. Navigation bar includes "Reading Library" link with badge count (e.g., "Reading [7]")
2. Badge displays count of `reading_queue` items with `reading_status = 'unread'`
3. Badge updates automatically via WebSocket OR polling (every 5-10 seconds during quiz session)
4. WebSocket implementation (RECOMMENDED):
   - Backend emits `reading_queue_updated` event with new `unread_count` when items added
   - Frontend listens and updates badge count reactively
   - No popup, toast, or notification shown (completely silent)
5. Polling fallback (if WebSocket not implemented in MVP):
   - Frontend polls GET `/api/v1/reading/stats` every 10 seconds during active quiz session
   - Response: `{unread_count: 7, high_priority_count: 3}`
   - Update badge silently
6. Badge styling: Small circular badge (8px border radius), orange/blue color, white text, positioned top-right of "Reading" text
7. Badge appears only when count >0, hidden when count = 0
8. Clicking badge/link navigates to Reading Library page (Story 5.7)
9. Unit tests: Badge count updates correctly when queue items added
10. Integration test: User answering questions sees badge count increment silently

#### Story 5.7: Reading Library Page with Queue Display

As a **user**,
I want to browse my reading queue in a dedicated library page,
so that I can read study materials when I'm ready, not when forced during quizzes.

**Acceptance Criteria:**
1. Dedicated page/route: `/reading-library` accessible from main navigation
2. GET `/api/v1/reading/queue?status=unread&sort_by=priority` retrieves user's reading queue
3. Query parameters supported:
   - `status=unread|reading|completed|dismissed|all` (default: unread)
   - `ka_id=uuid` (filter by Knowledge Area)
   - `priority=high|medium|low` (filter by priority)
   - `sort_by=priority|date|relevance` (default: priority)
4. Response includes array of queue items with:
   - `queue_id`, `chunk_id`, `title` (BABOK section name), `preview` (first 100 chars)
   - `babok_section` (e.g., "3.2.1"), `ka_name`, `relevance_score`, `priority`, `reading_status`
   - `word_count`, `estimated_read_minutes` (word_count / 200)
   - Context: `question_preview`, `was_incorrect`, `added_at`
5. Library page displays queue items as cards (14px border radius):
   - Priority badge (High = red, Medium = orange, Low = blue)
   - BABOK section title + preview
   - Knowledge Area tag
   - Context: "Added after incorrect answer on: [Question preview]" (shows why recommended)
   - Estimated read time (e.g., "2 min read")
   - "Read Now" button (primary CTA)
6. Tabs or filter bar: Unread (default) | Reading | Completed
7. Sort dropdown: Priority (default) | Date Added | Relevance Score
8. Filter by KA: Dropdown with 6 KA options + "All KAs"
9. Empty state: "Your reading library is empty. Complete quiz sessions to get personalized recommendations!"
10. Visual design: Framer-inspired, Inter font, cards (14px radius), main container (35px radius)
11. Accessibility: Cards keyboard navigable, screen reader announces priority and context
12. Unit tests: Library page renders, filters work
13. Integration test: User can browse queue and see all reading items

#### Story 5.8: Reading Item Detail View and Engagement Tracking

As a **user**,
I want to read individual BABOK chunks in detail and mark them as complete,
so that I can learn the material and track my reading progress.

**Acceptance Criteria:**
1. Clicking "Read Now" on queue item → navigate to detail view OR expand in-place (modal or dedicated page)
2. GET `/api/v1/reading/queue/{queue_id}` retrieves full chunk content
3. Response includes:
   - Full `text_content` (200-500 tokens, formatted markdown or plain text)
   - BABOK section reference, title, KA name
   - Context: Question that prompted recommendation
   - Previous reading history: `times_opened`, `total_reading_time_seconds`
4. Detail view displays:
   - Full reading content (readable formatting, proper line spacing, paragraph breaks)
   - BABOK section reference at top (e.g., "BABOK v3 - Section 3.2.1: Stakeholder Analysis")
   - Context card: "This was recommended because you answered [Question preview] incorrectly"
   - Actions: "Mark as Complete", "Dismiss", "Back to Library"
5. Track engagement automatically:
   - On view load → increment `times_opened`, set `first_opened_at` if first time
   - On view close/navigate away → calculate `time_spent_seconds` (time between load and close)
   - PUT `/api/v1/reading/queue/{queue_id}/engagement` with `time_spent_seconds`
   - Update `total_reading_time_seconds += time_spent_seconds`
6. "Mark as Complete" action:
   - PUT `/api/v1/reading/queue/{queue_id}/status` with `reading_status = 'completed'`
   - Set `completed_at` timestamp
   - Decrement unread badge count
   - Show success message: "Great! Added to your completed reading"
7. "Dismiss" action:
   - PUT `/api/v1/reading/queue/{queue_id}/status` with `reading_status = 'dismissed'`
   - Set `dismissed_at` timestamp
   - Remove from unread count
   - Show confirmation: "Dismissed. You can find this in Dismissed tab if needed."
8. **Bulk dismiss action:** POST `/api/v1/reading/queue/batch-dismiss` endpoint
   - Request body: `{"queue_ids": ["uuid1", "uuid2", "uuid3"]}`
   - Response: `{"dismissed_count": 3, "remaining_unread_count": 4}`
   - Use case: "Dismiss All Low Priority" button on library page
   - All specified queue_ids set to `reading_status = 'dismissed'` with single API call
9. Unit tests: Engagement tracking works, status updates correctly, batch dismiss works
10. Integration test: User can read content, mark complete, batch dismiss, and see badge count update

#### Story 5.9: Reading Queue Analytics and Completion Rates

As a **product team**,
I want to track reading queue engagement metrics,
so that we can validate the async reading model improves completion rates vs. inline reading.

**Acceptance Criteria:**
1. GET `/api/v1/reading/stats` endpoint returns complete user-level reading analytics
   - **Response schema** (see `docs/Asynchronous_Reading_Model.md` Lines 398-436 for complete spec):
   ```json
   {
     "reading_stats": {
       "total_items_added": 45,
       "total_completed": 28,
       "total_dismissed": 10,
       "current_unread": 7,
       "completion_rate": 0.62,
       "this_week": {
         "items_added": 7,
         "items_completed": 5,
         "total_reading_time_minutes": 25
       },
       "by_ka": [
         {
           "ka_name": "Business Analysis Planning and Monitoring",
           "unread": 3,
           "completed": 8,
           "completion_rate": 0.73
         }
       ],
       "average_reading_time_minutes": 2.5,
       "total_reading_time_hours": 1.2
     }
   }
   ```
   - Target: `completion_rate` >0.50 (50%+ per PRD v2.1 success criteria)
2. Dashboard integration: Display reading stats on main dashboard
   - "Reading Progress: X completed (Y% completion rate)"
   - "Total Reading Time: Z minutes"
3. Admin analytics endpoint GET `/api/admin/alpha-metrics/reading`:
   - Platform-wide reading completion rate
   - Comparison: Async model (v2.1) vs. Inline model (v2.0 baseline, if A/B tested)
   - Average reading time per chunk
   - Most frequently added BABOK sections (helps identify high-value content)
4. Track reading engagement by priority:
   - High priority items: Completion rate (expect highest)
   - Medium priority: Completion rate
   - Low priority: Completion rate (expect lowest)
5. Hypothesis validation metrics (Day 24 alpha test):
   - Async reading completion rate >50% (vs. 25% inline baseline per PRD)
   - User satisfaction with "read when ready" model (survey question)
6. Spaced repetition integration: Items marked "completed" should not re-appear in queue (unique constraint enforced)
7. Retention analysis: Users who complete reading have better long-term retention (tracked via spaced repetition accuracy)
8. Unit tests: Analytics calculations accurate
9. Integration test: Reading completion updates all analytics metrics
10. Performance: Analytics queries optimized with indexes on `reading_queue(user_id, reading_status)`

#### Story 5.10: Manual Reading Bookmarks for Post-Session Review (v2.1 NEW)

As a **user reviewing incorrect answers**,
I want to manually bookmark specific reading materials during post-session review for later study,
so that I can save high-priority content separately from the automatic reading queue.

**Context:** This story complements the automatic reading queue (Stories 5.5-5.9) by allowing users to explicitly bookmark materials they find particularly valuable during the post-session review phase. While the reading queue is auto-populated, bookmarks are user-initiated and signify higher intent to study specific content.

**Acceptance Criteria:**
1. **Database Schema:** Create `reading_bookmarks` table with the following structure:
   ```sql
   CREATE TABLE reading_bookmarks (
       bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
       chunk_id UUID NOT NULL REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,

       -- Context: What prompted this bookmark
       question_id UUID REFERENCES questions(question_id) ON DELETE SET NULL,
       session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
       review_id UUID REFERENCES session_reviews(review_id) ON DELETE SET NULL,

       -- State tracking
       is_read BOOLEAN DEFAULT FALSE,
       read_at TIMESTAMP,

       -- Timestamps
       bookmarked_at TIMESTAMP NOT NULL DEFAULT NOW(),

       CONSTRAINT fk_bookmark_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
       CONSTRAINT fk_bookmark_chunk FOREIGN KEY (chunk_id) REFERENCES content_chunks(chunk_id) ON DELETE CASCADE,
       CONSTRAINT unique_user_chunk_bookmark UNIQUE (user_id, chunk_id)
   );

   CREATE INDEX idx_reading_bookmarks_user ON reading_bookmarks(user_id);
   CREATE INDEX idx_reading_bookmarks_unread ON reading_bookmarks(user_id, is_read) WHERE is_read = FALSE;
   ```

2. **POST `/api/v1/reading/bookmarks` endpoint** - Create new bookmark
   - Request body: `{"chunk_id": "uuid", "question_id": "uuid", "session_id": "uuid", "review_id": "uuid"}`
   - Response: `201 Created` with `{"bookmark_id": "uuid", "chunk_id": "uuid", "bookmarked_at": "ISO8601"}`
   - Validation: Duplicate bookmarks return existing bookmark (idempotent), not 409 error
   - Business logic: If chunk already in user's reading_queue, mark it as bookmarked (add flag to reading_queue or separate tracking)

3. **GET `/api/v1/reading/bookmarks` endpoint** - Retrieve user's bookmarks
   - Query parameters:
     - `unread_only=true|false` (default: false) - Filter to unread bookmarks only
     - `ka_id=uuid` (optional) - Filter by Knowledge Area
     - `page=1` and `per_page=20` (pagination)
   - Response: Array of bookmark objects including:
     - `bookmark_id`, `chunk_id`, `title` (BABOK section name), `preview` (first 100 chars)
     - `babok_section` (e.g., "3.2.1"), `ka_name`, `word_count`, `estimated_read_minutes`
     - Context: `question_preview`, `session_id`, `review_id`, `bookmarked_at`
     - `is_read`, `read_at`
   - Pagination metadata: `total_items`, `total_pages`, `current_page`

4. **PUT `/api/v1/reading/bookmarks/{bookmark_id}/mark-read` endpoint** - Mark bookmark as read
   - Request: No body required
   - Response: `200 OK` with `{"bookmark_id": "uuid", "is_read": true, "read_at": "ISO8601"}`
   - Business logic: Set `is_read = TRUE`, `read_at = NOW()`

5. **DELETE `/api/v1/reading/bookmarks/{bookmark_id}` endpoint** - Remove bookmark
   - Response: `204 No Content`
   - Business logic: Soft delete or hard delete (decision: hard delete for MVP simplicity)

6. **Frontend Integration in Post-Session Review:**
   - When displaying reading material during review (Story 4.7), add "Save for Later" button next to each chunk
   - Clicking "Save for Later" → POST to `/api/v1/reading/bookmarks` → Visual confirmation ("Bookmarked!")
   - If chunk already bookmarked → show "Bookmarked ✓" (disabled state)

7. **Bookmarks Page/Section in Navigation:**
   - Add "Bookmarks" link in navigation (separate from "Reading Library")
   - Bookmarks page displays user's saved materials using GET `/api/v1/reading/bookmarks`
   - Tabs: "Unread Bookmarks" (default) | "All Bookmarks"
   - Each bookmark card shows same design as reading queue but with bookmark icon
   - Actions: "Read Now", "Mark as Read", "Remove Bookmark"

8. **Distinction from Reading Queue:**
   - Reading Queue (`reading_queue` table): Auto-populated, system-driven recommendations based on incorrect answers
   - Reading Bookmarks (`reading_bookmarks` table): User-initiated, manually saved high-value materials
   - Both can coexist: A chunk can be in both queue AND bookmarks (separate tables, separate tracking)
   - User benefit: Bookmarks provide a "favorites" layer on top of the queue for items requiring extra attention

9. **Analytics Tracking:**
   - Track bookmark creation rate: % of displayed reading chunks that get bookmarked (expect 10-20%)
   - Track bookmark read rate: % of bookmarks that get marked as read (target: 70%+, higher than queue)
   - Compare engagement: Bookmarked items should have higher completion rate than queue items (validates manual curation)

10. **Unit Tests:**
    - Create bookmark, retrieve bookmarks, mark as read, remove bookmark
    - Idempotent bookmark creation (duplicate returns existing)
    - Pagination works correctly
    - Filtering by unread_only and ka_id works

11. **Integration Tests:**
    - Full bookmark flow: Create → Retrieve → Mark Read → Delete
    - Bookmark during review session updates bookmarks list
    - Bookmarks persist across sessions

12. **Performance:**
    - Bookmark queries optimized with indexes on `user_id` and `is_read`
    - GET `/api/v1/reading/bookmarks` returns in <200ms for up to 100 bookmarks per user

**Success Metrics (30-day post-launch):**
- Bookmark adoption: 30%+ of users create at least 1 bookmark
- Bookmark read rate: 70%+ of bookmarks are marked as read (vs. 50% for queue items)
- Average bookmarks per active user: 5-10
- Bookmark-to-queue ratio: ~1:5 (users are selective about bookmarking)

**Relationship to Reading Queue:**
- Reading Queue (Stories 5.5-5.9): Broad net, auto-populated, may have false positives
- Reading Bookmarks (Story 5.10): Curated collection, user-verified relevance, higher intent
- Together: Queue provides discovery, Bookmarks provide focus

---

### Epic 6: Progress Dashboard & Transparency

**Epic Goal:** Provide users with comprehensive progress visibility through a real-time dashboard showing competency scores for all 6 KAs, exam readiness scoring, weekly progress trends, reviews due count, days until exam, and actionable recommendations. This epic delivers the transparency that builds user trust and engagement.

#### Story 6.1: Dashboard Overview with 6 KA Competency Bars

As a **user**,
I want to see my current competency scores for all 6 CBAP knowledge areas at a glance,
so that I understand exactly where I stand and which areas need focus.

**Acceptance Criteria:**
1. GET `/api/dashboard` endpoint returns user's current competency data (requires authentication)
2. Response includes:
   - `ka_scores`: Array of 6 objects with `ka_name`, `competency_score` (0-100%), `target_score`, `gap` (target - current)
   - `exam_readiness_score`: Overall readiness (0-100%, average or weighted average of 6 KAs)
   - `days_until_exam`: Calculated from onboarding `exam_date`
   - `reviews_due_count`: Number of concepts needing spaced repetition review (Epic 7 integration)
   - `total_questions_answered`: Lifetime count
   - `total_reading_consumed`: Number of chunks read
3. Dashboard UI displays 6 competency bars (horizontal bars or radial/circular charts):
   - Each bar shows KA name, current score (e.g., "Strategy Analysis: 75%"), target score (e.g., "Target: 85%")
   - Bar color-coded: Red (<70%), Orange (70-85%), Green (>85%)
   - Visual fill indicates progress toward target (e.g., bar filled 75% if score is 75%)
4. Hero metric: Exam Readiness Score displayed prominently (large text, color-coded, main screen container 35px radius)
5. Recommended focus areas: "Focus on [Lowest KA]" callout or section highlighting weakest 2-3 KAs
6. Visual design: Framer-inspired layout, Inter font, primary cards for KA bars (22px radius), main container (35px radius)
7. Accessibility: Bar charts have text labels (not color-only), screen reader announces competency scores
8. Unit tests: Dashboard data retrieval, competency scores displayed correctly
9. Integration test: Dashboard reflects competency updates from quiz sessions
10. Performance: Dashboard renders in <2 seconds with all data

#### Story 6.2: Weekly Progress Trends Chart

As a **user tracking my improvement**,
I want to see how my competency scores have changed week-over-week,
so that I stay motivated by visible progress.

**Acceptance Criteria:**
1. Backend calculates weekly competency snapshots:
   - Every 7 days (or weekly cron job), store snapshot of all 6 KA scores in `competency_history` table (user_id, snapshot_date, ka, competency_score)
   - Alternative: Calculate on-the-fly from `competency_tracking.last_updated` timestamps (if real-time snapshots not stored)
2. GET `/api/dashboard/trends` endpoint returns weekly progress data for last 4-8 weeks
3. Response: Array of weekly snapshots with date and 6 KA scores per week
4. Dashboard displays line chart or bar chart showing competency trends over time:
   - X-axis: Weeks (Week 1, Week 2, ...)
   - Y-axis: Competency score (0-100%)
   - Multiple lines/bars for each KA (6 lines or 6 grouped bars)
5. Chart highlights improvement: Positive deltas shown in green (e.g., "+5% this week"), negative in orange (rare, indicates need for review)
6. If user has <2 weeks of data, show message: "Complete more quiz sessions to unlock weekly progress trends"
7. Chart library: Recharts or Chart.js (as specified in Technical Assumptions)
8. Visual design: Chart card (22px radius), Inter font for labels, color scheme consistent with overall design
9. Accessibility: Chart data available in table format for screen readers (toggle view or aria-label with values)
10. Performance: Trends chart renders in <1 second (included in dashboard <2 second total)

#### Story 6.3: Exam Countdown and Readiness Indicators

As a **user preparing for a specific exam date**,
I want to see how many days I have until my exam and whether I'm on track to be ready,
so that I can adjust my study intensity if needed.

**Acceptance Criteria:**
1. Dashboard displays "Days Until Exam: X days" prominently (from onboarding `exam_date`)
2. If exam date is <30 days away: Display urgency indicator (orange/red color, "Less than 1 month!")
3. If exam date is <7 days away: Display critical urgency (red, "Exam in X days - final review!")
4. Exam readiness threshold: 75% average competency or all 6 KAs >70% (configurable)
5. Readiness status indicator:
   - **Ready:** Green checkmark, "You're exam-ready!" (all KAs >70% or average >75%)
   - **Almost Ready:** Orange icon, "Focus on [KA Names] to reach readiness" (1-2 KAs <70%)
   - **Not Ready:** Red icon, "Continue studying - X KAs below target" (3+ KAs <70%)
6. Pacing recommendations (future enhancement noted, not fully implemented in MVP):
   - If exam in 30 days and user <60% avg competency: "Consider increasing daily study time or adjusting exam date"
   - If user on track: "Great progress! Keep up daily sessions to maintain retention"
7. User can update exam date from settings (Story 8.2) if timeline changes
8. Visual design: Countdown and readiness status in hero section (main container 35px radius), clear color-coding
9. Accessibility: Color-coded status supplemented with text and icons (not color-only)
10. Unit tests: Countdown calculated correctly, readiness status accurate based on competency scores

#### Story 6.4: Knowledge Area Detail Drill-Down

As a **user wanting to understand my gaps in a specific KA**,
I want to drill down into a KA's detail view to see concept-level gaps and recent performance,
so that I can focus my studying on specific weaknesses within that KA.

**Acceptance Criteria:**
1. Dashboard KA bars are clickable (or have "View Details" button) → navigates to KA detail page
2. GET `/api/dashboard/ka/{ka_name}` endpoint returns detailed data for one KA:
   - `ka_name`, `competency_score`, `target_score`, `gap`
   - `concept_gaps`: Array of concepts within this KA with low performance (e.g., ["Stakeholder Analysis: 50%", "RACI Matrix: 60%"])
   - `recent_questions`: Last 10 questions answered in this KA with correctness (correct/incorrect)
   - `time_spent`: Total minutes spent studying this KA
   - `questions_answered`: Count of questions answered in this KA
3. KA detail view displays:
   - **Header:** KA name, current score, target, gap (primary card 22px radius)
   - **Concept Gaps:** List of weak concepts (if trackable, else generic "Review questions you missed")
   - **Recent Performance:** Visual timeline or list showing last 10 questions (green checkmark = correct, red X = incorrect)
   - **Time Spent:** "You've spent X minutes on this KA"
   - **Recommended Action:** "Focus on [specific concept]" or "Continue practicing [KA] questions"
4. Primary CTA: "Study [KA Name]" button → starts KA-focused quiz session (filter adaptive selection to this KA only)
5. Secondary CTA: "Back to Dashboard" link
6. Visual design: Detail page consistent with dashboard (Framer-inspired, Inter font, card styling)
7. Accessibility: Navigation breadcrumb (Dashboard > [KA Name]), keyboard-accessible back button
8. Unit tests: KA detail data retrieval, concept gaps calculated
9. Integration test: Clicking KA bar navigates to detail view, detail view reflects KA-specific data
10. Performance: KA detail view loads in <1 second

#### Story 6.5: Actionable Recommendations and CTAs

As a **user viewing my dashboard**,
I want clear recommendations on what to study next,
so that I don't waste time deciding and can immediately take action.

**Acceptance Criteria:**
1. Dashboard calculates actionable recommendations based on current state:
   - **If reviews due:** Primary CTA = "Start Reviews (X concepts due)" (Epic 7 integration)
   - **If no reviews due:** Primary CTA = "Continue Learning" → starts adaptive quiz session (Epic 4)
   - **If specific KA very weak (<60%):** Recommendation callout = "Priority: Focus on [KA Name] (scored X%)"
2. Recommendations section (card, 22px radius) displays:
   - **Top recommendation:** "Your next best step: [Action]"
   - **Secondary recommendations:** List of 2-3 suggested actions (e.g., "Review Strategy Analysis concepts", "Complete 10 more questions to unlock trends")
3. CTAs are pill-rounded buttons (primary color, high contrast)
4. If user completes primary recommendation (e.g., finishes reviews), dashboard updates CTA dynamically on next load
5. Recommendation logic documented: Based on reviews due > weakest KA > general quiz (priority hierarchy)
6. Visual design: Recommendations prominent but not overwhelming (balanced with competency visualizations)
7. Accessibility: CTA buttons have clear aria-labels ("Start 5 review questions now")
8. Unit tests: Recommendation logic selects appropriate CTA based on user state
9. Integration test: Dashboard shows correct CTA after completing quiz session or reviews
10. A/B testing placeholder (Phase 2): Track which recommendations drive most engagement

---

### Epic 7: Spaced Repetition & Long-Term Retention

**Epic Goal:** Implement the SM-2 spaced repetition algorithm to schedule concept reviews at optimal intervals (1, 3, 7, 14 days), ensuring users retain learned concepts through exam day. This epic delivers concept mastery tracking, review scheduling, mixed quiz sessions (reviews + new content), and reviews-due indicators on the dashboard.

#### Story 7.1: Concept Mastery Tracking for Spaced Repetition

As a **system**,
I want to track concept-level mastery state for each user,
so that spaced repetition can schedule reviews based on forgetting curve.

**Acceptance Criteria:**
1. Define concept mapping: Each question tagged with 1-3 `concept_tags` (e.g., ["stakeholder analysis", "RACI matrix"])
2. Create `concept_mastery` table: user_id, concept_tag, ka, ease_factor (default 2.5), interval_days (1/3/7/14), repetition_count, last_reviewed, next_review_due
3. After user answers question correctly for **first time**:
   - Create `concept_mastery` record for each concept_tag in that question
   - Set `interval_days = 1` (review in 1 day), `next_review_due = today + 1 day`
4. After user answers question incorrectly:
   - If concept_mastery exists: Reset `interval_days = 1`, `repetition_count = 0` (start over)
   - If concept_mastery doesn't exist: Do not create (only correct answers establish mastery)
5. SM-2 algorithm parameters: ease_factor adjusts based on performance (2.5 default, range 1.3-2.5)
6. Unit tests: Concept mastery created on first correct answer, reset on incorrect, not created on first incorrect
7. Integration test: Answering questions populates concept_mastery table correctly
8. Performance: Mastery tracking adds <50ms to answer submission (Story 4.3)
9. Concept tags reviewed: Ensure all questions have meaningful concept_tags (not generic "CBAP")
10. Algorithm documented in `/docs/algorithms.md` (SM-2 adaptation for 60-day timeline)

#### Story 7.2: SM-2 Review Scheduling

As a **system**,
I want to schedule concept reviews at increasing intervals based on SM-2 algorithm,
so that users review concepts just before they're likely to forget them.

**Acceptance Criteria:**
1. When user answers **review question correctly**:
   - Calculate new interval: `new_interval = previous_interval * ease_factor`
   - Progression: 1 day → 3 days → 7 days → 14 days (approximately, SM-2 formula may vary slightly)
   - Update `concept_mastery`: `interval_days = new_interval`, `next_review_due = today + new_interval`, increment `repetition_count`
2. When user answers **review question incorrectly**:
   - Reset to start: `interval_days = 1`, `next_review_due = today + 1`, `repetition_count = 0`
   - Optionally decrease `ease_factor` (make future intervals shorter if concept is difficult)
3. Ease factor adjustment (SM-2 quality rating simplified for MVP):
   - Correct answer: ease_factor stays same or increases slightly (+0.1, max 2.5)
   - Incorrect answer: ease_factor decreases (-0.2, min 1.3)
4. Maximum interval capped at 14 days (per Brief requirements for 60-day exam timeline)
5. Reviews due identification: Query `concept_mastery` where `next_review_due <= today`
6. Overdue prioritization: Reviews past due date prioritized over newly due reviews
7. Unit tests: Correct answer increases interval, incorrect resets interval, intervals follow ~1/3/7/14 progression
8. Integration test: Multiple review cycles produce expected interval progression
9. Performance: Review scheduling calculation <100ms (part of answer submission)
10. Monitor review accuracy: Target 70%+ correct on reviews (per Brief) - if lower, intervals may be too aggressive

#### Story 7.3: Mixed Quiz Sessions (Reviews + New Content)

As a **user with reviews due**,
I want quiz sessions to automatically mix review questions with new content,
so that I reinforce retention while continuing to learn new material.

**Acceptance Criteria:**
1. When user starts quiz session (Story 4.1), check if reviews are due:
   - Query `concept_mastery` where `next_review_due <= today` → count of concepts needing review
   - If reviews due: Create **mixed session** (40% reviews + 60% new content per Brief requirements)
   - If no reviews due: Create **new content session** (100% new questions)
2. Mixed session composition example: If user plans to answer 10 questions → 4 reviews + 6 new
3. Review question selection:
   - Select questions tagged with concepts due for review (from `concept_mastery.concept_tag`)
   - Prioritize overdue reviews (past `next_review_due` by most days)
   - If multiple questions match same concept, select one randomly
4. New question selection: Use adaptive logic from Story 4.2 (weakest KAs, difficulty matching)
5. Question order: Intermix reviews and new questions (not clustered - e.g., R, N, N, R, N, R, N, N, R, N)
6. Review questions labeled: "Review" badge or icon displayed on question card (visual distinction from new content)
7. Session type stored in `quiz_sessions` table: `session_type` = "mixed" or "new_content"
8. Unit tests: Mixed session has correct ratio (40/60), review questions selected from due concepts
9. Integration test: User with reviews due receives mixed session, user without reviews receives new content session
10. Performance: Mixed session creation in <500ms (review lookup + adaptive selection)

#### Story 7.4: Review Performance Tracking and Accuracy Metrics

As a **user completing review questions**,
I want my review accuracy tracked so I can see if I'm retaining concepts long-term,
so that I have confidence my retention is improving.

**Acceptance Criteria:**
1. After user answers **review question** (identified by "Review" label in session):
   - Update `concept_mastery` per SM-2 logic (Story 7.2)
   - Record in `quiz_responses` with `is_review = true` flag
2. Calculate review accuracy metrics:
   - **Overall Review Accuracy:** % of all review questions answered correctly (target 70%+ per Brief)
   - **Accuracy by Interval:** % correct on 1-day reviews, 3-day reviews, 7-day reviews, 14-day reviews
   - **Accuracy by KA:** % correct reviews per KA
3. GET `/api/progress/reviews` endpoint returns review metrics:
   - `overall_review_accuracy`, `accuracy_by_interval`, `accuracy_by_ka`
   - `reviews_completed_count`, `reviews_due_count`
4. Dashboard (Epic 6) displays review accuracy in a card (22px radius):
   - "Review Accuracy: X%" (color-coded: Green >70%, Orange 60-70%, Red <60%)
   - Breakdown by interval if user wants to drill down
5. If review accuracy <60%: Recommendation to slow down learning (more time per concept before advancing)
6. Unit tests: Review accuracy calculated correctly, breakdown by interval accurate
7. Integration test: Completing review questions updates accuracy metrics
8. Performance: Metrics calculation <200ms (part of dashboard load)
9. Alpha/Beta test validation: Monitor if users maintain >70% review accuracy (validates SM-2 intervals)
10. Adjustment mechanism (Phase 2): If accuracy consistently low, suggest adjusting intervals or adding extra review cycles

#### Story 7.5: Reviews Due Indicator on Dashboard

As a **user**,
I want to see how many review concepts are due on my dashboard,
so that I'm reminded to complete reviews and maintain retention.

**Acceptance Criteria:**
1. Dashboard (Story 6.1) displays "Reviews Due" count:
   - Query `concept_mastery` where `next_review_due <= today` → count
   - Display as badge or prominent metric (e.g., "5 Reviews Due")
2. Visual treatment:
   - If reviews due: Orange/yellow color (attention, not alarming), icon (refresh/repeat symbol)
   - If no reviews due: Green checkmark, "No reviews due - great job!"
3. Clicking "Reviews Due" badge → starts mixed quiz session (Story 7.3) prioritizing reviews
4. Primary CTA on dashboard adapts (Story 6.5):
   - If reviews due: "Start Reviews (X concepts)" becomes primary action
   - If no reviews: "Continue Learning" is primary
5. Reviews due count updates in real-time after completing mixed session
6. If reviews overdue (past due by >2 days): Escalate visual treatment (red color, "X overdue reviews")
7. Unit tests: Reviews due count accurate, dashboard CTA adapts correctly
8. Integration test: Completing reviews reduces reviews due count on dashboard
9. Visual design: Reviews due indicator styled as secondary card (14px radius) or inline badge
10. Email reminders (Phase 2, not MVP): Daily email if reviews due >3 and user hasn't logged in

---

### Epic 8: Polish, Testing & Launch Readiness

**Epic Goal:** Complete platform polish with user settings, profile management, accessibility compliance (WCAG 2.1 AA), comprehensive error handling, production deployment configuration, and alpha test readiness. This epic ensures the platform is stable, accessible, and ready for the Day 30 case study user launch.

#### Story 8.1: User Profile and Account Management

As a **user**,
I want to view and update my profile information and preferences,
so that I can keep my account details current and adjust my learning goals.

**Acceptance Criteria:**
1. GET `/api/user/profile` returns user profile data:
   - `email`, `created_at`, `onboarding_data` (7 questions answered), `exam_date`, `target_score`, `daily_time_commitment`
2. Settings page displays:
   - **Account section:** Email (editable), Password (change password option)
   - **Preferences section:** Exam date (date picker), Target score (70/80/90%), Daily time commitment (30-60 min / 1-2 hrs / 2+ hrs)
   - **Display Preferences:** Dark mode toggle (Light / Dark / Auto) - NEW MVP FEATURE
   - **Data & Privacy:** View privacy policy, Export my data, Delete account
3. PUT `/api/user/profile` updates editable fields (email, exam_date, target_score, daily_time_commitment)
4. Email change validation: Must be valid email, unique in database (409 Conflict if duplicate)
5. Password change: POST `/api/user/change-password` accepts `current_password`, `new_password`
   - Verify current password correct (401 if wrong)
   - Validate new password (8+ chars, letter + number)
   - Update hashed password in database
6. Exam date change: Recalculates "days until exam" on dashboard immediately
7. **Dark Mode Toggle:** Segmented control or dropdown with 3 options: Light / Dark / Auto (system preference)
   - Default: Auto mode (follows system preference via `prefers-color-scheme` media query)
   - Saved to user profile: `PUT /api/user/profile` with `theme_preference` field ('light' | 'dark' | 'auto')
   - Theme persists across devices and sessions (retrieved from user profile on login)
   - Root HTML class toggle: `<html class="light">` or `<html class="dark">`
   - 200ms color transition when toggling (prevents jarring flash)
   - **Complete dark mode specifications:** See `/docs/front-end-spec.md` Lines 2193-2227
8. Settings page styled consistent with dashboard (Framer-inspired, Inter font, form cards 22px radius, pill-rounded buttons)
9. Success messages: "Profile updated successfully", "Password changed successfully", "Theme preference updated"
10. Unit tests: Profile retrieval, profile update, password change, dark mode toggle, validation errors
11. Integration test: User can update preferences and changes persist across sessions, dark mode syncs across devices

#### Story 8.2: Data Export and Account Deletion

As a **user concerned about data privacy**,
I want to export my data and have the option to delete my account completely,
so that I maintain control over my personal information (GDPR readiness).

**Acceptance Criteria:**
1. GET `/api/user/export` endpoint generates JSON export of all user data:
   - User profile (email, created_at, onboarding_data)
   - Competency scores (all 6 KAs, historical snapshots)
   - Quiz responses (all questions answered, timestamps, correctness)
   - Reading history (chunks read, engagement data)
   - Concept mastery state (spaced repetition data)
2. Export downloaded as `learnr_data_{user_id}_{date}.json` file (client-side download trigger)
3. DELETE `/api/user/account` endpoint deletes user account and all associated data:
   - Soft delete or hard delete (hard delete for MVP to truly remove data)
   - Cascade delete: Remove from `users`, `onboarding_data`, `competency_tracking`, `quiz_responses`, `concept_mastery`, `reading_history`, etc.
   - Confirmation step: Frontend shows modal "Are you sure? This cannot be undone. Type DELETE to confirm"
4. After deletion: User logged out, JWT invalidated, redirect to landing page with message "Account deleted successfully"
5. Settings page: "Export My Data" button (downloads JSON), "Delete Account" button (opens confirmation modal)
6. Privacy policy link: Links to `/privacy` page (static page with LearnR privacy policy)
7. Terms of service link: Links to `/terms` page (static page with terms)
8. Unit tests: Data export includes all user data, account deletion removes all records
9. Integration test: Full export → delete → verify user cannot log in and data removed from database
10. Compliance: GDPR right to be forgotten satisfied (user can delete all data)

#### Story 8.3: WCAG 2.1 Level AA Accessibility Compliance

As a **user with disabilities**,
I want the platform to be fully accessible via keyboard and screen reader,
so that I can use LearnR regardless of visual or motor impairments.

**Acceptance Criteria:**
1. **Keyboard Navigation:**
   - All interactive elements (buttons, links, form inputs, cards) accessible via Tab key
   - Tab order is logical (follows visual flow: top to bottom, left to right)
   - Focus indicators visible on all focusable elements (2px outline, high contrast color)
   - Enter/Space keys activate buttons and links
   - Escape key closes modals and dropdowns
2. **Screen Reader Compatibility:**
   - Semantic HTML: Use `<button>`, `<nav>`, `<main>`, `<section>`, `<article>` appropriately
   - ARIA labels on interactive elements: `aria-label` for icon buttons, `aria-describedby` for form field hints
   - Alt text on all images/icons (or `aria-hidden="true"` for decorative elements)
   - Form labels properly associated with inputs (`<label for="email">`)
   - Screen reader announcements for dynamic content (e.g., "Correct answer" announced after quiz submission)
3. **Color Contrast:**
   - Text contrast ratio: 4.5:1 for normal text (Inter font), 3:1 for large text (18pt+)
   - Button contrast: Primary buttons have 3:1 contrast with background
   - Visual indicators not color-only: Use icons + text (e.g., green checkmark + "Correct", not just green)
4. **Text Resizing:**
   - Page remains functional when text resized to 200% (browser zoom or font size increase)
   - No horizontal scrolling required, content reflows responsively
5. **No Flashing Content:** No animations or transitions flash >3 times per second (seizure risk)
6. **Descriptive Links:** Link text is descriptive (not "click here"), e.g., "View Knowledge Area details"
7. **Accessibility Audit Tools:**
   - Run axe DevTools or WAVE on all key pages (landing, dashboard, quiz, settings)
   - Fix all Critical and Serious issues flagged
   - Document any Minor issues deferred to Phase 2
8. Manual testing: Navigate entire quiz flow using only keyboard (no mouse)
9. Screen reader testing: Use NVDA (Windows) or VoiceOver (Mac) to navigate dashboard and quiz
10. README documents accessibility commitment and how to report issues

#### Story 8.4: Error Handling and User-Friendly Messages

As a **user encountering errors**,
I want clear, helpful error messages that guide me to resolution,
so that I'm not frustrated or confused when something goes wrong.

**Acceptance Criteria:**
1. **API Error Responses:** Standardized JSON format:
   ```json
   {
     "error": "ValidationError",
     "message": "Password must be at least 8 characters with letter and number",
     "field": "password"
   }
   ```
2. **Frontend Error Display:**
   - Inline validation errors on forms (red text below field, e.g., "Email already exists")
   - Toast/snackbar notifications for global errors (e.g., "Network error, please try again")
   - Modal dialogs for critical errors (e.g., "Session expired, please log in again")
3. **Error Categories:**
   - **400 Bad Request:** Validation errors → show specific field error
   - **401 Unauthorized:** Session expired → redirect to login with message
   - **403 Forbidden:** Access denied → "You don't have permission to access this"
   - **404 Not Found:** Resource not found → "Question not found" or "Page not found"
   - **409 Conflict:** Duplicate resource → "Email already registered"
   - **500 Internal Server Error:** Server error → "Something went wrong. Please try again or contact support."
4. **Network Errors:** Offline or timeout → "Connection lost. Check your internet and try again."
5. **Retry Logic:** Transient errors (500, network timeout) automatically retry 1-2 times before showing error to user
6. **Error Logging:** All errors logged server-side with context (user_id, endpoint, request payload, stack trace) for debugging
7. **User Support Link:** All error messages include "Contact Support" link (opens email or help page)
8. **Loading States:** Spinners or skeleton screens during API calls (prevent user thinking app is frozen)
9. Unit tests: Error responses formatted correctly, frontend displays appropriate messages
10. Integration test: Simulate various errors (validation, auth, network) and verify user sees helpful messages

#### Story 8.5: Production Deployment and Environment Configuration

As a **DevOps engineer**,
I want the application deployed to production with proper environment configuration and monitoring,
so that the platform is stable and accessible for the case study user launch.

**Acceptance Criteria:**
1. **Frontend Deployment:**
   - Deploy React app to Vercel or Netlify (per Technical Assumptions)
   - Environment variables: `VITE_API_URL` (backend URL), `VITE_ENV` (production)
   - Custom domain configured (e.g., `app.learnr.com`)
   - HTTPS enforced (SSL certificate auto-provisioned)
   - Build optimized: Code splitting, minification, gzip compression
2. **Backend Deployment:**
   - Deploy FastAPI to Railway or Render (containerized deployment)
   - Environment variables: `DATABASE_URL` (PostgreSQL), `QDRANT_URL`, `OPENAI_API_KEY`, `JWT_SECRET_KEY`, `ENV=production`
   - Health check endpoint `/health` monitored by platform
   - Auto-scaling configured (start with 1 instance, scale up if load >80% CPU)
3. **Database:**
   - PostgreSQL managed service (Railway/Render Postgres or similar)
   - Daily automated backups with 7-day retention
   - Connection pooling configured (max 10 connections for MVP)
4. **Qdrant:**
   - Self-hosted Qdrant via Docker on backend server (cost $0)
   - Alternative: Migrate to Qdrant Cloud if performance issues (budget $50-100/month approved)
   - Qdrant data persisted to volume (survives container restart)
5. **CI/CD Pipeline:**
   - GitHub Actions workflow triggers on push to `main` branch
   - Run tests (unit + integration) → if pass, deploy to production
   - Deployment rollback capability (revert to previous version if issues detected)
6. **Monitoring:**
   - Error tracking: Sentry or similar integrated (capture all 500 errors, unhandled exceptions)
   - Uptime monitoring: UptimeRobot or similar pings `/health` every 5 minutes
   - Alerts: Email/Slack notification if health check fails or error rate >5%
7. **Performance:**
   - Frontend initial load <3 seconds (verified with Lighthouse)
   - Backend API response times <500ms for quiz questions, <1 second for reading content
8. README documents deployment process, environment variables, and rollback procedure
9. Smoke tests: After deployment, manually verify key flows (register, login, quiz, dashboard)
10. Case study user access: Provide login credentials, confirm user can access production app

#### Story 8.6: Alpha Test Readiness and Day 24 Go/No-Go Preparation

As a **product manager**,
I want all alpha test instrumentation and success criteria tracking in place,
so that we can make a data-driven Go/No-Go decision on Day 24.

**Acceptance Criteria:**
1. **Alpha Test Instrumentation:**
   - Reading engagement tracking (Story 5.3) fully functional
   - Reading relevance feedback (Story 5.4) fully functional
   - Explanation helpfulness feedback (Story 4.5) fully functional
   - Review accuracy tracking (Story 7.4) fully functional
2. **Success Metrics Dashboard (Internal, not user-facing):**
   - GET `/api/admin/alpha-metrics` endpoint returns:
     - Reading engagement rate (% chunks expanded vs. displayed) - target 60%+
     - Reading relevance rate (% thumbs up) - target 80%+
     - Explanation helpfulness (% thumbs up) - target 85%+
     - Review accuracy (% correct) - target 70%+
     - Daily active usage (% of days user logged in) - target 80%+
3. **Case Study User Onboarding:**
   - User account created, onboarding completed, diagnostic taken (baseline established)
   - User provided with clear instructions: "Complete daily sessions for next 30 days, exam Dec 21"
   - Feedback mechanism: User can send feedback anytime (email, in-app form, or scheduled check-ins)
4. **Day 24 Alpha Test:**
   - Schedule user interview/survey on Day 24 (November 14, 2025 if launch Nov 21)
   - Survey questions:
     - "How relevant was the BABOK reading content to your gaps?" (1-5 scale)
     - "Did the reading content help you understand concepts better?" (Yes/Somewhat/No)
     - "Would you recommend LearnR over static quiz apps?" (Yes/No, why?)
     - "Do you plan to continue using LearnR for the remaining 30 days?" (Yes/No)
   - Go criteria (from Brief):
     - ✓ User finds BABOK reading content valuable (80%+ helpful rating)
     - ✓ User commits to daily usage for remaining 30 days
     - ✓ User can articulate differentiation vs. static quiz apps
5. **No-Go Plan:**
   - If reading content not valued: Iterate UX (make more prominent, improve relevance) OR pivot strategy (focus on adaptive quiz only)
   - If user not committing to continued usage: Diagnose blockers (UX issues, time commitment, feature gaps)
6. **Alpha Test Documentation:**
   - `/docs/alpha_test_plan.md` outlines schedule, metrics, Go/No-Go criteria
   - Daily progress log: Track user engagement, issues reported, feedback collected
7. Unit tests: Admin metrics endpoint returns accurate alpha test data
8. Integration test: Full alpha test flow simulated (onboarding → diagnostic → quiz → reading → reviews)
9. Stakeholder readiness: Product team briefed on Day 24 decision process
10. Contingency time: Days 25-30 available for iteration if No-Go (adjust features, re-test)

#### Story 8.7: Admin Support Tools for Alpha Test

As a **platform administrator**,
I want to search for users, impersonate their sessions, and view their analytics in PostHog,
so that I can provide support during alpha test and debug user-reported issues.

**Acceptance Criteria:**

1. **Admin Role Management:**
   - `users` table includes `is_admin` boolean column (default: false)
   - Admin users designated via direct database flag (no self-service promotion)
   - Only users with `is_admin = true` can access admin endpoints

2. **Admin Middleware:**
   - Implement `@require_admin` decorator/middleware extending JWT auth
   - Check `is_admin` claim in decoded JWT
   - Return 403 Forbidden if user not admin
   - All `/api/admin/*` endpoints protected by this middleware

3. **User Search:**
   - GET `/api/admin/users/search?q={query}` endpoint
   - Searches across: email (partial match), user_id (exact), name (if stored)
   - Response: Array of user objects with:
     - `user_id`, `email`, `created_at`, `onboarding_completed`, `exam_date`, `last_login_at`
   - Pagination: `?limit=20&offset=0` (default 20 results)
   - Sorting: `?sort_by=created_at&order=desc`

4. **User Impersonation:**
   - POST `/api/admin/impersonate/{user_id}` endpoint
   - Validates: user_id exists, requester is admin
   - Generates new JWT with:
     - `user_id`: target user's ID (not admin's)
     - `impersonated_by`: admin's user_id
     - `exp`: 30 minutes from now (short-lived token)
   - Response: `{access_token, user_email, expires_in_seconds}`
   - Frontend stores impersonation token separately from admin token

5. **Impersonation Session UI:**
   - Frontend detects impersonation token (checks for `impersonated_by` claim)
   - Displays persistent banner at top of ALL pages:
     - Background: Orange/yellow (high visibility)
     - Text: "🔍 Viewing as user@email.com"
     - Button: "Exit Impersonation" (pill-rounded, secondary)
   - Banner not dismissible (always visible during impersonation)
   - All API calls use impersonation token (user sees their actual data)

6. **Exit Impersonation:**
   - POST `/api/admin/impersonate/exit` endpoint
   - Invalidates impersonation token
   - Frontend switches back to admin's original token
   - Redirect to admin dashboard or user search

7. **Impersonation Audit Trail:**
   - Create `admin_audit_log` table:
     - `id`, `admin_user_id`, `action_type`, `target_user_id`, `metadata` (JSONB), `timestamp`
   - Log events: "impersonation_started", "impersonation_ended"
   - Metadata includes: `duration_seconds`, `ip_address`, `user_agent`
   - GET `/api/admin/audit-log` returns recent admin actions (for compliance)

8. **PostHog Integration:**
   - PostHog SDK configured in backend and frontend
   - User events tracked with `user_id` as distinct_id (PostHog identifier)
   - Admin user search results include "View in PostHog" link:
     - URL format: `https://app.posthog.com/person/{user_id}` (or PostHog-specific URL)
     - Opens in new tab
   - Link styled as tertiary action (icon: analytics)

9. **Security Safeguards:**
   - Impersonation tokens cannot impersonate other admins (403 if target user is admin)
   - Rate limiting on impersonation: Max 10 impersonations per admin per hour
   - Email notification to user if impersonated (optional, configurable)
   - Admin cannot modify user data during impersonation (read-only mode recommended, or log all changes)

10. **Testing:**
    - Unit tests: Admin middleware blocks non-admin, allows admin
    - Unit tests: Impersonation token generation includes correct claims
    - Integration test: Admin can search user, impersonate, view dashboard as user, exit
    - Integration test: PostHog link renders correctly on user search results
    - Security test: Non-admin cannot access `/api/admin/*` endpoints

**Admin UI Specifications:**

This story defines admin functional requirements. Detailed admin UI specifications should be documented in `/docs/front-end-spec.md` including:

- **Admin User Search Screen:** Layout, search bar, results table, action buttons
- **Impersonation Banner Component:** Persistent orange banner design, exit button placement
- **Admin Dashboard:** (if separate from main dashboard) user list, metrics, audit log access
- **PostHog Link Integration:** Icon, tooltip, visual styling

**Recommended Frontend Spec Addition:**
Add "Screen 9: Admin Support Interface" section with ASCII wireframes for:
1. User search page layout
2. Impersonation banner (shown across all pages during impersonation)
3. Admin dashboard (if needed)

See Story 8.7 Acceptance Criteria above for complete functional requirements.

---

## PM Checklist Validation Report

### Executive Summary

**Overall PRD Completeness:** 99% ✓
**MVP Scope Appropriateness:** Just Right ✓
**Readiness for Architecture Phase:** READY ✓

The LearnR PRD is comprehensive, well-structured, and provides exceptional clarity for the architecture and implementation phases. The document successfully balances MVP focus with necessary detail, covering all critical aspects from problem definition through epic-level implementation guidance.

**Key Strengths:**
- Exceptionally detailed user stories (56 stories, 520+ acceptance criteria)
- Clear problem-solution fit with measurable success criteria
- Comprehensive technical assumptions guiding architecture
- MVP scope tightly focused on validation (30-day timeline, Day 24 Go/No-Go)
- Sequential epic structure with clear dependencies and rationale
- Admin support tools for alpha test operations (impersonation, user search, PostHog integration)

**Minor Gaps (Non-Blocking):**
- Visual diagrams for user flows and architecture (recommended for Architect to create)
- Detailed stakeholder communication plan (addressed informally via alpha test)

### Category Status Table

| Category                         | Status  | Critical Issues                         |
| -------------------------------- | ------- | --------------------------------------- |
| 1. Problem Definition & Context  | PASS    | None - Clear problem, validated solution|
| 2. MVP Scope Definition          | PASS    | None - Scope tight, rationale documented|
| 3. User Experience Requirements  | PASS    | None - Flows, accessibility, performance covered|
| 4. Functional Requirements       | PASS    | None - Comprehensive FR1-FR18 + epic stories|
| 5. Non-Functional Requirements   | PASS    | None - Performance, security, reliability specified|
| 6. Epic & Story Structure        | PASS    | None - 8 epics, 56 stories, 520+ ACs   |
| 7. Technical Guidance            | PASS    | None - Architecture, tech stack, testing clear|
| 8. Cross-Functional Requirements | PASS    | None - Data, integrations, operations, admin tools covered|
| 9. Clarity & Communication       | PARTIAL | Minor: No visual diagrams, informal stakeholder plan|

**Overall Status:** ✅ **PASS (99% Complete)**

### Recommendations

**For Architect (Architecture Phase):**
1. Create visual diagrams (system architecture, data model ERD, deployment architecture)
2. Decide on deferred technical choices (Context API vs. Redux, UI component library)
3. Create Technical Specification Document building on this PRD

**For UX Expert (Design Phase):**
1. Create user flow diagrams (onboarding, learning loop, dashboard)
2. Design high-fidelity mockups following UI Design Goals (Framer-inspired, Inter font, pill buttons, border radius hierarchy)
3. Create design system/style guide (colors, typography, components, accessibility)

**For Development Team (Implementation Phase):**
1. Follow Epic sequence 1→8 (dependencies documented in Epic Sequencing Rationale)
2. Track progress against 56 user stories (~6 stories/day for 30-day MVP)
3. Prepare for Day 24 alpha test checkpoint (Go/No-Go on reading feature)
4. Maintain 70%+ unit test coverage for business-critical code
5. Implement admin support tools (Story 8.7) for operational support during alpha test

**Admin Functionality Scope Clarification:**
- **MVP includes:** User impersonation, user search, PostHog deep links, admin audit trail (Story 8.7)
- **Deferred to future:** Course creation wizard, revenue tracking, platform analytics dashboard (see admin-user-flows.md for future specifications)

### Final Decision

✅ **READY FOR ARCHITECT**

The LearnR PRD demonstrates complete requirements coverage (99%), appropriate MVP scope (30-day achievable), implementation readiness (56 stories with 520+ ACs), and technical clarity (architecture, tech stack, testing, risks well-documented).

**Confidence Level:** Very High - This PRD sets a strong foundation for successful MVP delivery.

**Next Steps:**
1. Hand off to **UX Expert** for design phase
2. Hand off to **Architect** for technical specification
3. Schedule architecture and design review meeting
4. Proceed to development sprint planning

---

## References

### Foundational Documents
- **Project Brief:** docs/brief.md (2,347 lines - comprehensive problem, solution, goals, validation approach)
- **Project Decisions Log:** docs/note.md (200+ documented decisions)

### v2.1 Feature Specifications (EXISTING)
- **Implementation Summary:** docs/Implementation_Summary.md (964 lines - master guide for Post-Session Review & Async Reading Library)
- **Async Reading Architecture:** docs/Asynchronous_Reading_Model.md (1,050 lines - complete reading queue system architecture)
- **Learning Loop Spec:** docs/Learning_Loop_Refinement.md (1,488 lines - post-session review feature specification)

### UX/UI Specifications (EXISTING)
- **Frontend Specification:** docs/front-end-spec.md (1,801 lines - complete UI/UX spec, design system, components)
- **User Flows:** docs/user-flows.md (747 lines - detailed user flow diagrams in Mermaid format)

### Additional Product Documentation (EXISTING)
- **Admin User Flows:** docs/admin-user-flows.md (future admin dashboard and course management workflows - partial MVP scope in Story 8.7: user impersonation, search, PostHog integration)
- **Product Summary:** docs/Product_Summary_for_Stakeholders.md (stakeholder-facing summary)

### Technical Documentation (TBD by Architect)
- **Database Schema:** docs/TDDoc_DatabaseSchema.md (comprehensive schema with v2.1 tables)
- **Algorithm Documentation:** docs/TDDoc_Algorithms.md (IRT, SM-2, adaptive selection, priority calculation)
- **Data Models:** docs/TDDoc_DataModels.md (all entities, relationships, constraints)
- **API Documentation:** docs/TDDoc_API_Endpoints.md (consolidated API contract specification)

---

## Next Steps

This PRD is now complete and ready for the next phases. The recommended sequence is **UX Design** (parallel track) and **Architecture** (parallel track), followed by **Development**.

---

### Prompt for UX Expert

**Context:** You are the UX Expert agent responsible for designing the user experience and visual design for LearnR, an adaptive learning platform for CBAP exam preparation.

**Your Task:**
Create a comprehensive UX Design Document based on the LearnR PRD (docs/prd.md). Your design should bring the requirements to life with user flows, wireframes, high-fidelity mockups, and a complete design system.

**IMPORTANT - Existing Documentation:**
A detailed Frontend Specification already exists at **`docs/front-end-spec.md`** (1,801 lines). Additionally, comprehensive user flows are documented in **`docs/user-flows.md`** (747 lines). Your task is to:
1. Review these existing specifications for completeness and quality
2. Validate alignment with PRD requirements (especially v2.1 features: Post-Session Review, Async Reading Library)
3. Enhance and refine where needed
4. Create visual mockups and design system assets (Figma files)
5. **DO NOT recreate specifications from scratch** - build upon the extensive work already documented

**Key Inputs from PRD:**
1. **UI Design Goals** (Section: User Interface Design Goals)
   - Overall UX Vision: "Personal learning coach" feel
   - Key Interaction Paradigms: Progressive disclosure (onboarding), focused assessment mode (quiz), data dashboard (progress), contextual content (reading)
   - Core Screens: 9 critical screens identified
   - Design Specs:
     - Font: Inter (primary typeface, weights 400/500/600/700)
     - Icons: Vector icons ONLY (no emojis anywhere)
     - Design Inspiration: Framer website templates
     - Border Radius Hierarchy: Main containers (35px), primary cards (22px), secondary cards (14px), icons (8-12px)
     - Buttons: Pill-rounded (border-radius: 9999px or 50%)
     - Layout: 8px grid system for consistent spacing
   - Color Psychology: Professional blue (primary), green (success), warm orange (attention), clean grays/whites
   - Accessibility: WCAG 2.1 Level AA compliance (keyboard nav, screen reader, 4.5:1 contrast, text resizing 200%)
   - Platforms: Web responsive (desktop 1280x720+, tablet 768x1024, mobile 375x667+)

2. **User Journeys** (Section: User Experience Principles → Critical User Flows)
   - First-Time User Journey: Landing + inline Q1 → Q2-7 → Account creation → Diagnostic (12 questions) → Results + dashboard → First quiz + reading → Return to dashboard
   - Daily Active User Journey: Login → Dashboard (reviews due?) → Start reviews OR new quiz → Quiz loop (question → answer → explanation → reading → next) → Return to dashboard

3. **Core Screens to Design** (from UI Design Goals):
   - Landing Screen with Inline First Question
   - Onboarding Flow (Questions 2-7)
   - Account Creation Screen
   - Diagnostic Assessment Screen (12 questions, focused mode)
   - Diagnostic Results Screen (6 KA bars, gap analysis, exam readiness)
   - Progress Dashboard (home screen with 6 KA bars, exam readiness, reviews due, trends)
   - Knowledge Area Detail View (drill-down for specific KA)
   - Quiz Session Screen (question display, answer selection)
   - Explanation & Reading Screen (feedback, detailed explanation, BABOK chunks)
   - Settings/Profile Screen (account, preferences, privacy)

**Your Deliverables:**
1. **User Flow Diagrams** (visual flowcharts for key journeys using tools like Figma, Miro, or Whimsical)
2. **Wireframes** (low-fidelity layouts for all 9 core screens)
3. **High-Fidelity Mockups** (polished designs for key screens: Landing, Dashboard, Quiz, Results) following Framer-inspired aesthetic
4. **Design System / Style Guide**:
   - Color palette (hex codes for primary blue, success green, attention orange, neutrals)
   - Typography scale (Inter font sizes, weights, line heights)
   - Component library (buttons, cards, form inputs, progress bars, charts, icons)
   - Spacing system (8px grid multiples)
   - Accessibility guidelines (contrast ratios, focus states, aria-labels)
5. **Interaction Patterns Document** (animations, transitions, hover states, loading states, error states)

**Design Constraints:**
- NO emojis - use vector icons instead (recommend library: Heroicons, Feather Icons, or Lucide)
- Pill-rounded buttons (border-radius: 9999px)
- Hierarchical border radius for cards (35px/22px/14px/8-12px)
- WCAG 2.1 AA compliance (test with axe DevTools or similar)
- Mobile-first responsive design (works from 375px width up)

**Output:**
Create a UX Design Document (docs/ux-design.md or Figma file) that developers can reference during implementation. Include links to Figma prototypes or image exports of mockups.

---

### Prompt for Architect

**Context:** You are the Architect agent responsible for creating the technical specification for LearnR, an adaptive learning platform for CBAP exam preparation.

**Your Task:**
Create a comprehensive Technical Specification Document based on the LearnR PRD (docs/prd.md). Your specification should define the system architecture, data models, API contracts, deployment strategy, and provide implementation guidance for the development team.

**IMPORTANT - Existing Technical Specifications:**
Detailed technical specifications for v2.1 features already exist. You MUST review these documents as foundational inputs:
- **`docs/Implementation_Summary.md`** (964 lines) - Master implementation guide covering database schemas, API contracts, and feature specifications for Post-Session Review and Asynchronous Reading Library
- **`docs/Asynchronous_Reading_Model.md`** (1,050 lines) - Complete technical architecture for the reading queue system
- **`docs/Learning_Loop_Refinement.md`** (1,488 lines) - Phase-by-phase specification of the post-session review feature with detailed flowcharts

Your task is to consolidate these specifications into a unified Technical Specification Document and add missing architectural elements (system diagrams, deployment architecture, algorithm specifications).

**Key Inputs from PRD:**
1. **Technical Assumptions** (Section: Technical Assumptions)
   - Repository Structure: Monorepo (`/frontend`, `/backend`, `/shared`, `/scripts`, `/docs`)
   - Service Architecture: Monolithic FastAPI backend (defer microservices until >1,000 concurrent users)
   - Technology Stack:
     - **Frontend:** React 18+, TypeScript, Vite, Context API (or Redux if needed)
     - **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0+, Pydantic
     - **Databases:** PostgreSQL 15+ (relational), Qdrant (vector embeddings)
     - **External APIs:** OpenAI (GPT-4, text-embedding-3-large)
   - Testing Requirements: Unit + Integration testing (70%+ coverage for business-critical), manual E2E for MVP
   - Deployment: Frontend (Vercel/Netlify), Backend (Railway/Render), PostgreSQL (managed service), Qdrant (self-hosted Docker)
   - CI/CD: GitHub Actions (test → deploy on push to `main`)

2. **Data Model Requirements** (from Epic Stories):
   - **Users:** id, email, hashed_password, created_at, updated_at
   - **Onboarding Data:** user_id FK, referral_source, certification, motivation, exam_date, knowledge_level, target_score, daily_study_time
   - **Questions:** id, question_text, option_a/b/c/d, correct_answer, explanation, ka, difficulty, concept_tags JSONB, source, created_at
   - **BABOK Chunks:** chunk_id, ka, section_ref, difficulty, concept_tags JSONB, text_content TEXT
   - **Diagnostic Responses:** user_id FK, question_id FK, selected_answer, timestamp
   - **Quiz Responses:** user_id FK, session_id FK, question_id FK, selected_answer, is_correct, is_review BOOL, time_taken, timestamp
   - **Competency Tracking:** user_id FK, ka, competency_score FLOAT, last_updated
   - **Concept Mastery:** user_id FK, concept_tag, ka, ease_factor FLOAT, interval_days INT, repetition_count INT, last_reviewed, next_review_due
   - **Reading History:** user_id FK, chunk_id FK, marked_read BOOL, timestamp
   - **Reading Engagement:** user_id FK, chunk_id FK, session_id FK, displayed_at, expanded_at, time_spent_seconds, marked_read
   - **Quiz Sessions:** session_id, user_id FK, start_time, end_time, session_type (new_content | mixed), questions_answered_count, is_paused, is_completed

3. **API Endpoints to Define** (from Epic Stories):
   - **Authentication:** POST /api/auth/register, POST /api/auth/login, POST /api/auth/forgot-password, POST /api/auth/reset-password
   - **User Profile:** GET /api/user/profile, PUT /api/user/profile, POST /api/user/change-password, POST /api/user/onboarding, GET /api/user/export, DELETE /api/user/account
   - **Diagnostic:** GET /api/diagnostic/questions, POST /api/diagnostic/answer, GET /api/diagnostic/results
   - **Quiz:** POST /api/quiz/session/start, GET /api/quiz/session/{id}, POST /api/quiz/session/{id}/pause, POST /api/quiz/session/{id}/end, POST /api/quiz/answer
   - **Content:** GET /api/content/questions, POST /api/content/reading
   - **Dashboard:** GET /api/dashboard, GET /api/dashboard/trends, GET /api/dashboard/ka/{ka_name}
   - **Progress:** GET /api/progress/reviews
   - **Reading:** POST /api/reading/track, POST /api/reading/engagement
   - **Feedback:** POST /api/feedback/explanation, POST /api/feedback/reading, POST /api/feedback/report
   - **Health:** GET /health
   - **Admin (Support Tools):** GET /api/admin/users/search, POST /api/admin/impersonate/{user_id}, POST /api/admin/impersonate/exit, GET /api/admin/audit-log, GET /api/admin/alpha-metrics

4. **Performance Requirements** (from Technical Assumptions):
   - Question display: <500ms after answer submission
   - Reading content retrieval: <1 second (vector search + PostgreSQL join)
   - Dashboard rendering: <2 seconds (aggregate all 6 KA scores + trends)
   - Database queries: Indexed on user_id, question_id, session_id for fast lookups

5. **Security Requirements**:
   - Password hashing: bcrypt or Argon2
   - JWT expiration: 7-day token expiration
   - HTTPS only (all production traffic over TLS)
   - Input validation: Pydantic models validate all API inputs
   - Rate limiting: Implement on auth endpoints (prevent brute force)

**Your Deliverables:**
1. **System Architecture Diagram** (components: Frontend → Backend API → PostgreSQL, Qdrant → External APIs: OpenAI)
2. **Data Model ERD** (Entity-Relationship Diagram showing all tables, relationships, foreign keys, indexes)
3. **API Contract Specification** (OpenAPI 3.0 spec or detailed endpoint documentation):
   - For each endpoint: Method, Path, Request Body Schema, Response Schema, Status Codes, Error Responses
4. **Deployment Architecture Diagram** (Frontend hosting, Backend hosting, Database services, CI/CD pipeline)
5. **Algorithm Specifications** (docs/TDDoc_Algorithms.md):
   - Simplified IRT competency calculation formula
   - Adaptive question selection algorithm (pseudocode)
   - SM-2 spaced repetition scheduling logic
6. **Testing Strategy Document**:
   - Unit test structure (what to test, coverage targets)
   - Integration test approach (API endpoint testing, database integration)
   - E2E test scenarios (manual for MVP)
7. **Technical Debt Register**:
   - Simplified IRT (full 3-parameter IRT deferred to Phase 2)
   - Manual E2E testing (automation deferred)
   - When to extract microservices (threshold: >1,000 concurrent users)

**Technical Decisions Deferred to You:**
1. **Frontend State Management:** Context API (recommended for simplicity) vs. Redux Toolkit (if complex state)
2. **UI Component Library:** Material-UI, Chakra UI, or custom components (recommend MUI or Chakra for speed)
3. **Chart Library:** Recharts or Chart.js (for progress dashboard visualization)
4. **Email Service:** SendGrid, AWS SES, or similar (for password reset, future notifications)

**Output:**
Create a Technical Specification Document (docs/tech-spec.md) that developers can reference during implementation. Include diagrams (export from Lucidchart, draw.io, or Mermaid markdown), data models, and API contracts.

---

**Recommended Next Workflow:**
Run both UX Design and Architecture phases in **parallel** (they have minimal dependencies), then proceed to Development Sprint Planning with outputs from both
- Purpose: Define technical architecture, system design, technology choices
- Note: Epic breakdown created after will have full technical context

### Recommended Path

**For LearnR:**
1. **UX Design** (critical for learning app experience)
2. **Architecture** (technical design for adaptive engine + AI integration)
3. **Epic Breakdown** (with full UX + Architecture context)
4. **Solutioning Gate Check** (validate cohesion before implementation)
5. **Sprint Planning** (begin implementation)

---

## Version 2.1 Enhancement Summary (November 19, 2025)

### Overview of New Features

This version adds two major features that significantly enhance learning effectiveness and user experience:

1. **Post-Session Review** - Immediate reinforcement of incorrect answers
2. **Asynchronous Reading Library** - Zero-interruption, on-demand study materials

### Key Design Decisions (Approved)

| Decision # | Decision | Rationale |
|------------|----------|-----------|
| **#84** | Implement post-session review feature | Research shows immediate correction improves retention 2-3x vs delayed review only |
| **#85** | Make review optional but encouraged | User autonomy leads to better engagement than forced behavior |
| **#86** | Implement asynchronous reading model | Zero interruption to learning flow; reading becomes valuable resource not penalty |
| **#87** | Use silent badge updates (no toasts) | Truly zero interruption; no notification fatigue; cleaner UX |

### Database Schema Additions

**New Tables (3):**

1. **`session_reviews`** - Tracks post-session review completion
   - review_id (PK), session_id (FK), user_id (FK)
   - total_questions_to_review, questions_reinforced_correctly, questions_still_incorrect
   - review_status (not_started | in_progress | completed | skipped)
   - review_started_at, review_completed_at

2. **`review_attempts`** - Individual question re-attempts during review
   - review_attempt_id (PK), review_id (FK), original_attempt_id (FK)
   - question_id (FK), user_id (FK), selected_choice_id (FK)
   - is_correct, is_reinforced (incorrect → correct)
   - time_spent_seconds, attempted_at

3. **`reading_queue`** - Asynchronous reading materials queue
   - queue_id (PK), user_id (FK), chunk_id (FK)
   - question_id (FK), session_id (FK), was_incorrect
   - relevance_score (0.00-1.00), priority (high | medium | low), ka_id (FK)
   - reading_status (unread | reading | completed | dismissed)
   - times_opened, total_reading_time_seconds
   - first_opened_at, completed_at, dismissed_at

4. **`admin_audit_log`** - Admin action audit trail for compliance
   - id (PK), admin_user_id (FK → users.id)
   - action_type (impersonation_started | impersonation_ended | user_search | etc.)
   - target_user_id (FK → users.id, nullable)
   - metadata (JSONB - duration_seconds, ip_address, user_agent, query, etc.)
   - created_at (timestamp)

**Table Updates:**

- **`users`** - Add `is_admin` boolean column (default: false) for admin role management

### API Endpoints Additions

**Post-Session Review (4 endpoints):**
- `POST /v1/sessions/{session_id}/review/start` - Start review phase
- `POST /v1/sessions/{session_id}/review/answer` - Submit review answer
- `POST /v1/sessions/{session_id}/review/complete` - Complete review
- `POST /v1/sessions/{session_id}/review/skip` - Skip review

**Reading Library (5 endpoints):**
- `GET /v1/reading/queue` - Get reading queue with filters
- `GET /v1/reading/queue/{queue_id}` - Get full content
- `PUT /v1/reading/queue/{queue_id}/status` - Mark complete/dismissed
- `POST /v1/reading/queue/batch-dismiss` - Bulk dismiss
- `GET /v1/reading/stats` - Reading analytics

**Total:** 9 new API endpoints

### User Experience Changes

**Learning Flow (Zero Interruption):**
```
Before: Question → Answer → Feedback → [READING BLOCKS] → Next
After:  Question → Answer → Feedback → [Reading added silently] → Next
```

**Post-Session Flow:**
```
Session Ends → Review Transition → Re-answer Incorrect Questions →
Review Summary → Return to Dashboard
```

**Reading Access:**
```
Anytime: Navigation → Reading Library [7] → Browse/Filter/Read →
Mark Complete/Dismiss
```

### Expected Impact (30-Day Post-Launch)

| Metric | Current | Target | Change |
|--------|---------|--------|--------|
| Avg Questions/Session | 12 | 18 | **+50%** |
| Session Completion | 65% | 80% | **+23%** |
| Reading Completion | 25% | 50% | **+100%** |
| User Satisfaction | 3.8/5 | 4.4/5 | **+16%** |
| 30-Day Retention | 60% | 70% | **+17%** |
| Weekly Reading Time | 8 min | 18 min | **+125%** |

### Implementation Timeline

- **Sprint 1 (Weeks 1-2):** Backend foundation (database + APIs)
- **Sprint 2 (Weeks 3-4):** Frontend implementation (UI components)
- **Sprint 3 (Weeks 5-6):** Integration & testing (E2E flows)
- **Sprint 4 (Weeks 7-8):** Analytics & beta launch (10% of users)

**Total:** 8 weeks to production

### Additional Documentation

Complete technical specifications available in:
- `/docs/Implementation_Summary.md` - Master implementation guide (700+ lines)
- `/docs/Asynchronous_Reading_Model.md` - Technical deep dive (600+ lines)
- `/docs/Learning_Loop_Refinement.md` - Review feature spec (500+ lines)
- `/docs/user-flows.md` - Updated user flows (Flows 4, 4b, 9)

**Total:** 2,000+ lines of production-ready specifications

### Key Innovation: "Test Fast, Read Later"

This update embodies the principle of **separating cognitive modes**:
- **Testing** = Active recall, momentum-driven, fast-paced
- **Reading** = Comprehension, thoughtful, self-paced
- **Review** = Immediate reinforcement, focused correction

By respecting these different mental states and giving users complete control, LearnR maximizes both engagement and learning effectiveness.

---

## Cross-Reference Index

**🎉 This PRD is now FULLY SELF-CONTAINED for critical specifications.**

All essential implementation details are included directly in this document:
- ✅ **Complete database schemas** (SQL DDL with all tables, indexes, constraints)
- ✅ **Complete algorithm pseudocode** (6 core algorithms with detailed logic)
- ✅ **Complete design system tokens** (colors, typography, spacing, CSS variables)
- ✅ **API versioning strategy** (v1 prefix, deprecation protocol)
- ✅ **Success metrics with baselines** (v2.0 → v2.1 improvement targets)

Supporting documents provide **supplementary details** for specific areas. Use this index to find additional context where needed.

### What's Self-Contained in This PRD

| Specification | PRD Section | Status |
|---------------|-------------|--------|
| **Database Schemas** | Database Schema Summary (15 tables with SQL) | ✅ Complete |
| **Core Algorithms** | Algorithm Specifications (6 algorithms with pseudocode) | ✅ Complete |
| **Design Tokens** | UI Design Goals → Design System Tokens | ✅ Complete |
| **Color Palettes** | Light mode (17 colors) + Dark mode (12 colors) with hex codes | ✅ Complete |
| **Typography Scale** | 8-level system (H1 → Caption) with weights and line heights | ✅ Complete |
| **Spacing System** | 7-level system (xs → 3xl) with rem values | ✅ Complete |
| **API Versioning** | Technical Assumptions → API Versioning Strategy | ✅ Complete |
| **Success Metrics** | Success Criteria → v2.1 Feature Validation table | ✅ Complete |

### Supplementary Documentation (Optional Reference)

These documents provide additional context but are NOT required for implementation:

| Supplementary Detail | Document | Purpose |
|----------------------|----------|---------|
| **Component Library** | `docs/front-end-spec.md` Lines 1273-2074 | 13 pre-designed component specifications with variants |
| **Screen Wireframes** | `docs/front-end-spec.md` Lines 328-1076 | ASCII wireframes for 10+ screens |
| **User Flow Diagrams** | `docs/user-flows.md` Flows 4, 4b, 9 | Mermaid diagrams of user journeys |
| **Accessibility Details** | `docs/front-end-spec.md` Lines 2349-2440 | WCAG 2.1 AA implementation checklist |
| **Animation Details** | `docs/front-end-spec.md` Lines 2541-2643 | 8 animation patterns with timing/easing |
| **Loading & Error States** | `docs/front-end-spec.md` Lines 1077-1174 | 8 loading patterns, 8 error scenarios |
| **Filter UI Designs** | `docs/front-end-spec.md` Lines 787-872 | Reading Library filter layouts (desktop/tablet/mobile) |
| **Post-Session Review Flowcharts** | `docs/Learning_Loop_Refinement.md` | Phase-by-phase specification with detailed diagrams |
| **ERD Diagrams** | `docs/TDDoc_DatabaseSchema.md` | Entity relationship diagrams (visual representation of schemas already in PRD) |

### Key API Endpoint References

All API endpoints use `/v1/` prefix. Complete specifications in Epic story acceptance criteria.

| Endpoint Category | Example Endpoints | PRD Location |
|-------------------|-------------------|--------------|
| **Authentication** | POST /v1/auth/login, /v1/auth/register | Epic 1 Stories 1.1-1.3 |
| **Quiz** | POST /v1/quiz/answer, GET /v1/quiz/session/{id} | Epic 4 Stories 4.1-4.5 |
| **Reading Queue** | GET /v1/reading/queue, POST /v1/reading/queue/batch-dismiss | Epic 5 Stories 5.7-5.8 |
| **Reading Stats** | GET /v1/reading/stats | Epic 5 Story 5.9 |
| **User Profile** | GET /v1/user/profile, PUT /v1/user/profile | Epic 8 Story 8.1 |
| **Admin** | GET /v1/admin/users/search, POST /v1/admin/impersonate/{id} | Epic 8 Story 8.7 |

### Development Workflow (Self-Contained PRD)

**For Software Architects:**
1. **This PRD is sufficient** - All critical specifications (schemas, algorithms, design tokens) included
2. Read PRD sections:
   - Database Schema Summary → Complete SQL DDL for all 15 tables
   - Algorithm Specifications → 6 core algorithms with full pseudocode
   - Technical Assumptions → Architecture, API versioning, deployment
3. **Optional:** Reference `docs/front-end-spec.md` for screen wireframes and component library details

**For Backend Developers:**
1. **This PRD is sufficient** - No external documents required
2. Read PRD sections:
   - Database Schema Summary → All tables, indexes, constraints
   - Algorithm Specifications → Implementation-ready pseudocode
   - Epic Stories → Feature requirements and API endpoints
   - Technical Assumptions → Architecture decisions
3. **Optional:** Reference `docs/Learning_Loop_Refinement.md` for post-session review flowcharts

**For Frontend Developers:**
1. **This PRD is sufficient for core implementation**
2. Read PRD sections:
   - UI Design Goals → Design System Tokens (complete color/typography/spacing specs)
   - Epic Stories → Feature requirements and acceptance criteria
   - Dark Mode Typography Specifications → Enhanced readability guidelines
3. **Optional:** Reference `docs/front-end-spec.md` for:
   - Pre-designed component library (13 components)
   - Screen wireframes (10+ ASCII layouts)
   - Detailed accessibility checklist

### Document Versioning

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| `docs/prd.md` | 2.2 | 2025-11-19 | **Authoritative** - Single source of truth |
| `docs/Asynchronous_Reading_Model.md` | 2.1.0 | 2025-11-19 | Specification - Referenced by PRD |
| `docs/front-end-spec.md` | 1.0 | 2025-11-19 | Specification - Referenced by PRD |
| `docs/Implementation_Summary.md` | - | 2025-11-19 | Master guide - Referenced by PRD |
| `docs/Learning_Loop_Refinement.md` | - | 2025-11-19 | Specification - Referenced by PRD |

**Maintenance Protocol:**
- **PRD is the single source of truth** - All critical implementation specifications included directly
- Supporting documents provide supplementary context (wireframes, flowcharts, ERDs)
- When conflicts arise: **PRD takes precedence** - supporting docs are supplementary only
- Updates: Modify PRD first, then optionally update supporting docs for consistency

---

## Document Status

**✅ FULLY SELF-CONTAINED PRD**

This document contains ALL critical specifications needed for implementation:
- 15 complete database table schemas with SQL DDL
- 6 core algorithms with implementation-ready pseudocode
- Complete design system (17 light mode colors + 12 dark mode colors, 8 typography levels, 7 spacing levels)
- All Epic stories with acceptance criteria
- API versioning strategy and endpoint specifications
- Success metrics with baseline comparisons

**Document Stats:**
- **Total Lines:** 4,500+
- **Database Tables:** 15 (with complete SQL)
- **Algorithms:** 6 (with full pseudocode)
- **Color Tokens:** 29 (light + dark mode)
- **Epic Stories:** 50+ (across 8 epics)
- **Acceptance Criteria:** 500+

**Supporting Documents (Optional):**
- Component library designs
- Screen wireframes
- User flow diagrams
- Accessibility checklists
- ERD visual diagrams

---

_This PRD is the **complete capability contract** for LearnR - an AI-powered adaptive learning platform that transforms professional certification preparation through intelligent assessment, personalized content delivery, and scientifically-proven retention techniques._

_The platform delivers accurate competency tracking, adaptive difficulty, immediate reinforcement, asynchronous reading content, and spaced repetition to help working professionals achieve 80%+ first-time pass rates with 30% less study time._

_**Version 2.3 (SELF-CONTAINED):** Fully incorporated database schemas, algorithm pseudocode, and design system tokens. PRD now serves as the authoritative single source of truth with all critical implementation specifications included directly._

_Created through collaborative discovery between Developer and AI facilitator, informed by comprehensive Product Brief and 200+ documented project decisions._
