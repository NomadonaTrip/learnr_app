# Content Quality & Moderation

**Purpose:** Ensure question and reading content accuracy, relevance, and quality through systematic review and user feedback loops.

### Content Lifecycle

```
[Creation] → [Review] → [Publication] → [Monitoring] → [Update/Retire]
```

### Question Content Management

#### 1. Vendor Questions (Gold Standard)

**Source:** 500 CBAP questions from certified exam prep vendors

**Validation Process:**
- [ ] Verified by CBAP-certified subject matter expert (SME)
- [ ] Mapped to specific BABOK v3 sections
- [ ] Difficulty level assigned (1-5) based on SME assessment
- [ ] Explanations reviewed for accuracy and clarity
- [ ] Distractors (incorrect options) validated as plausible but incorrect

**Quality Metrics:**
- Target correctness rate: 50-70% (questions too easy or too hard flagged for review)
- User feedback rating: >80% "helpful"
- Report rate: <2% of users flag as incorrect

#### 2. LLM-Generated Questions (Variations)

**Generation Process:**
```python
# Prompt template for GPT-4
generate_question_variation(
    base_question=vendor_question,
    knowledge_area=ka,
    difficulty=difficulty,
    variation_type="rephrasing" | "context_change" | "difficulty_adjust"
)
```

**Review Workflow:**

| Stage | Reviewer | Criteria | SLA |
|-------|----------|----------|-----|
| **1. Auto-Validation** | GPT-4 self-check | Grammatical correctness, answer key consistency | Instant |
| **2. Similarity Check** | Qdrant vector search | Ensure variation is unique (>0.3 distance from base) | <1s |
| **3. Human Review** | CBAP SME (contract) | Content accuracy, BABOK alignment | 48 hours |
| **4. Pilot Testing** | Alpha user cohort | Correctness rate, user feedback | 7 days |

**Approval Criteria:**
- [ ] Passes similarity threshold (not duplicate)
- [ ] SME approves content (accuracy verified)
- [ ] Pilot correctness rate: 40-80% (within acceptable range)
- [ ] Zero "report as incorrect" flags during pilot

**Post-Launch Monitoring:**
- Questions with >90% correctness → Flag as "too easy", consider difficulty increase
- Questions with <30% correctness → Flag for review (possibly ambiguous or incorrect)
- Questions with >5% report rate → Immediate SME review

#### 3. User Feedback Mechanism

**In-App Feedback:**

```tsx
// After answer submission
<div className="feedback-actions">
  <button onClick={() => rateExplanation('helpful')}>
    👍 Helpful Explanation
  </button>
  <button onClick={() => rateExplanation('unhelpful')}>
    👎 Needs Improvement
  </button>
  <button onClick={() => openReportModal()}>
    🚩 Report Incorrect Question
  </button>
</div>
```

**Report Modal:**
```tsx
interface QuestionReport {
  question_id: UUID;
  user_id: UUID;
  issue_type: 'incorrect_answer' | 'ambiguous_wording' | 'outdated_content' | 'typo' | 'other';
  description: string;
  suggested_fix?: string;
  submitted_at: timestamp;
}
```

**Report Triage:**
- Reports auto-tagged by issue type
- Questions with 2+ reports in 7 days → Escalated to SME review queue
- High-severity reports (incorrect answer) → Immediate notification to content team
- Question temporarily hidden if 5+ reports in 24 hours (emergency removal)

### Reading Content Management

#### BABOK v3 Content Chunking

**Chunking Strategy:**
- Chunk size: 200-500 tokens (1-2 paragraphs)
- Chunk boundaries: Respect heading structure, don't break mid-concept
- Overlap: 50-token overlap between adjacent chunks (context preservation)

**Metadata Tagging:**
```python
chunk = {
    "id": UUID,
    "title": "5.2.4 Define Solution Scope",
    "content": "Markdown text...",
    "babok_section": "5.2.4",
    "knowledge_area": "Requirements Analysis and Design Definition",
    "concept_tags": ["Solution Scope", "Requirements", "Stakeholders"],
    "difficulty": 3,  # 1-5 scale
    "estimated_read_time_minutes": 4,
    "source": "BABOK v3 (2015)",
}
```

**Quality Assurance:**
- [ ] All chunks reference valid BABOK sections
- [ ] Concept tags align with exam blueprint
- [ ] No chunks <100 tokens (too short, lacks context)
- [ ] No chunks >800 tokens (too long, overwhelming)
- [ ] Reading time estimate validated (200 words/minute baseline)

#### Content Updates (BABOK Version Changes)

**Update Workflow:**
- Monitor IIBA for BABOK version releases
- On new version: Identify changed sections via diff analysis
- Update affected chunks within 30 days
- Notify users of content updates via in-app banner
- Maintain version history (rollback capability)

### Content Moderation Workflows

#### Daily Content Health Check (Automated)

```python
# Scheduled task: Daily 2am UTC
async def daily_content_health_check():
    # Flag questions with anomalous metrics
    flagged_questions = await db.execute("""
        SELECT id, text, avg_correct_rate, report_count
        FROM questions
        WHERE (avg_correct_rate < 0.30 OR avg_correct_rate > 0.90)
           OR report_count >= 2
           AND created_at > NOW() - INTERVAL '7 days'
    """)

    # Send report to content team
    await send_email(
        to="content@learnr.com",
        subject=f"Content Health Report - {flagged_questions.count()} Issues",
        body=generate_report(flagged_questions)
    )
```

#### Weekly SME Review (Manual)

**Agenda:**
- Review flagged questions from automated checks
- Review user reports (triage by severity)
- Approve pending LLM-generated questions
- Plan content updates for next sprint

**Approval Process:**
- SME marks questions as: "Approve", "Edit Required", "Retire"
- Edits applied by content editor
- Retired questions soft-deleted (historical data preserved)

### Content Metrics Dashboard (Admin)

**Key Metrics:**
- Total questions: 1,000 (500 vendor + 500 LLM)
- Average correctness rate by KA
- Questions flagged for review (count + list)
- User feedback sentiment (% helpful)
- Report resolution time (target: <48 hours)
- Content freshness (last BABOK update date)

**Admin UI:**
```
┌────────────────────────────────────────────────┐
│ Content Quality Dashboard                      │
├────────────────────────────────────────────────┤
│ Total Questions: 1,000                         │
│ Flagged for Review: 12                         │
│ Pending User Reports: 8                        │
│                                                │
│ Questions by Status:                           │
│  ✓ Active: 980                                 │
│  ⚠ Under Review: 12                            │
│  🚫 Retired: 8                                 │
│                                                │
│ User Feedback:                                 │
│  👍 Helpful: 87%                               │
│  👎 Needs Improvement: 10%                     │
│  🚩 Reported: 3%                               │
└────────────────────────────────────────────────┘
```

---
