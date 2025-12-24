# Story Lifecycle Pipeline Orchestrator

<!-- Powered by BMAD Core -->

## Purpose

Orchestrate the complete story lifecycle from backlog to commit, coordinating SM, PO, Dev, and QA agents with human-in-the-loop (HITL) checkpoints for quality assurance.

## Pipeline Overview

```
BACKLOG → SM(draft) → PO(validate) → [HITL#1] → DEV(implement) → QA(review) → [HITL#2] → DEV(fix) → [HITL#3] → COMMIT
```

## Inputs

```yaml
required:
  - sprint_backlog: 'docs/prd/sprint-backlog.md'
  - state_file: '.bmad-core/state/pipeline-state.json'
optional:
  - story_id: '{epic}.{story}' # Specific story to process (e.g., "4.5")
  - resume: boolean # Resume from checkpoint
  - status: boolean # Just show current status
```

## Prerequisites

- `.bmad-core/core-config.yaml` exists and is configured
- `docs/prd/sprint-backlog.md` exists with current sprint defined
- Epic files exist for stories in the sprint

---

## SEQUENTIAL Task Execution

### Phase 0: Initialization

#### 0.1 Load Configuration

- Load `.bmad-core/core-config.yaml`
- Extract: `devStoryLocation`, `prd.*`, `architecture.*`, `qa.*`
- If config missing, HALT: "core-config.yaml not found. Pipeline cannot proceed."

#### 0.2 Load Pipeline State

- Read `.bmad-core/state/pipeline-state.json`
- If `--status` flag: Display current state and exit
- If `--resume` flag: Jump to current checkpoint (Phase 4.2, 5.2, or 6.2)

#### 0.3 Select Target Story

**If `story_id` provided:**
- Validate story exists in sprint backlog
- Set as target story

**If no `story_id`:**
- Parse `docs/prd/sprint-backlog.md`
- Find "Current Sprint" section
- Select first story with `Pipeline: 📋 backlog` status
- If no eligible stories: HALT "No stories ready in pipeline. All stories are either in progress, blocked, or complete."

#### 0.4 Validate Story Dependencies

- Check story dependencies from backlog
- If dependencies not complete: HALT "Story {id} is blocked by incomplete dependencies: {deps}"

#### 0.5 Initialize Pipeline State

```json
{
  "pipeline": {
    "status": "running",
    "phase": "drafting",
    "checkpoint": null,
    "startedAt": "{now}"
  },
  "currentStory": "{story_id}",
  "stories": {
    "{story_id}": {
      "state": "drafting",
      "timestamps": { "entered": "{now}" }
    }
  }
}
```

- Update `sprint-backlog.md`: Set story Pipeline column to `📝 drafting`
- Log: "Pipeline started for story {story_id}"

---

### Phase 1: Story Drafting (SM Agent)

#### 1.1 Invoke SM Agent

- Execute task: `.bmad-core/tasks/create-next-story.md`
- Pass story_id to task
- SM Agent will:
  - Read epic definition
  - Gather architecture context
  - Create full story draft at `{devStoryLocation}/{epic}.{story}.story.md`
  - Run story-draft-checklist

#### 1.2 Capture SM Output

- Wait for SM Agent completion
- Capture story file path and summary
- Update state:
  ```json
  {
    "stories": {
      "{story_id}": {
        "state": "validating",
        "storyFile": "{path}",
        "timestamps": { "drafted": "{now}" },
        "agents": { "sm": { "status": "complete", "output": "{summary}" } }
      }
    }
  }
  ```
- Update `sprint-backlog.md`: Pipeline → `🔍 validating`
- Log: "SM Agent completed story draft"

---

### Phase 2: Story Validation (PO Agent)

#### 2.1 Invoke PO Agent

- Execute task: `.bmad-core/tasks/validate-next-story.md`
- Pass story file path
- PO Agent will:
  - Validate template completeness
  - Check file structure and source tree
  - Verify acceptance criteria
  - Check anti-hallucination
  - Generate validation report
  - **AMEND story file as needed** (critical difference from original task)

#### 2.2 Capture Amendments

- Wait for PO Agent completion
- Parse validation report for:
  - GO/NO-GO status
  - Amendments made
  - Issues found
- If NO-GO with critical issues:
  - Log issues
  - Set state to `failed`
  - HALT pipeline with detailed error

#### 2.3 Prepare HITL #1 Checkpoint Data

```json
{
  "checkpointData": {
    "checkpoint": "po_approval",
    "storyId": "{story_id}",
    "storyTitle": "{title}",
    "summary": "PO validation complete. {amendment_count} amendments made.",
    "validationStatus": "GO",
    "validationScore": 8,
    "amendments": [
      {
        "section": "Acceptance Criteria",
        "change": "Added AC for error handling",
        "reason": "Missing edge case"
      }
    ],
    "options": [
      { "key": "approve", "label": "Approve & Continue to Dev", "action": "continue" },
      { "key": "changes", "label": "Request More Changes", "action": "pause" },
      { "key": "abort", "label": "Abort Pipeline", "action": "abort" }
    ]
  }
}
```

---

### Phase 3: HITL Checkpoint #1 - PO Approval

#### 3.1 Pause for User Approval

- Update state:
  ```json
  {
    "pipeline": {
      "status": "checkpoint",
      "phase": "validating",
      "checkpoint": "po_approval"
    }
  }
  ```
- Update `sprint-backlog.md`: Pipeline → `⏳ awaiting_po_approval`

#### 3.2 Display Checkpoint UI

Present to user:

```
═══════════════════════════════════════════════════════════════════
  🛑 HITL CHECKPOINT #1: PO Validation Complete
═══════════════════════════════════════════════════════════════════

Story: {story_id} - {story_title}
Status: {GO/NO-GO} (Score: {score}/10)

📝 AMENDMENTS MADE BY PO:
┌─────────────────────────────────────────────────────────────────┐
│ Section              │ Change                                   │
├─────────────────────────────────────────────────────────────────┤
│ Acceptance Criteria  │ Added AC for error handling              │
│ Dev Notes            │ Added missing API endpoint spec          │
└─────────────────────────────────────────────────────────────────┘

📄 Story File: {story_file_path}

What would you like to do?

  [1] ✅ Approve & Continue to Development
  [2] 📝 Request More Changes (pause pipeline)
  [3] ❌ Abort Pipeline

Enter choice (1/2/3):
```

#### 3.3 Handle User Response

**If Approve (1):**
- Update state: `approved`, checkpoint: null
- Update `sprint-backlog.md`: Pipeline → `✅ approved`
- Continue to Phase 4

**If Request Changes (2):**
- Update state: `paused`
- Log: "Pipeline paused for user changes. Run /workflow-story-pipeline --resume when ready."
- HALT (user will manually edit and resume)

**If Abort (3):**
- Update state: `failed`, error: "Aborted by user at HITL #1"
- Update `sprint-backlog.md`: Pipeline → `📋 backlog`
- HALT

---

### Phase 4: Implementation (Dev Agent)

#### 4.1 Invoke Dev Agent

- Update state: phase → `implementing`
- Update `sprint-backlog.md`: Pipeline → `💻 implementing`
- **CRITICAL: The Dev Agent should implement the story based on the story file**
- Dev Agent responsibilities:
  - Read story file completely
  - Implement all acceptance criteria
  - Write unit tests
  - Run tests to ensure passing
  - Update story file with implementation notes

#### 4.2 Monitor Implementation

- Wait for Dev Agent completion
- Capture:
  - Files created/modified
  - Test results
  - Any errors or issues
- Update state:
  ```json
  {
    "stories": {
      "{story_id}": {
        "state": "qa_review",
        "timestamps": { "implemented": "{now}" },
        "agents": { "dev": { "status": "complete", "output": "{summary}" } }
      }
    }
  }
  ```

---

### Phase 5: QA Review (QA Agent)

#### 5.1 Invoke QA Agent

- Update state: phase → `qa_review`
- Update `sprint-backlog.md`: Pipeline → `🧪 qa_review`
- Execute task: `.bmad-core/tasks/review-story.md`
- Pass story file and implementation details
- QA Agent will:
  - Review code quality
  - Check test coverage
  - Validate acceptance criteria
  - Perform refactoring if needed
  - Generate QA gate file

#### 5.2 Capture QA Results

- Wait for QA Agent completion
- Parse QA gate file for:
  - Gate status (PASS/CONCERNS/FAIL)
  - Issues found
  - Recommendations
- Update state with QA results

#### 5.3 Prepare HITL #2 Checkpoint Data

```json
{
  "checkpointData": {
    "checkpoint": "qa_approval",
    "storyId": "{story_id}",
    "storyTitle": "{title}",
    "summary": "QA review complete. Gate: {status}",
    "qaFindings": {
      "gate": "CONCERNS",
      "issues": [...],
      "testsPass": true,
      "coveragePercent": 85
    },
    "options": [
      { "key": "approve", "label": "Approve (Accept as-is)", "action": "continue" },
      { "key": "fix", "label": "Fix Issues First", "action": "fix" },
      { "key": "abort", "label": "Abort Pipeline", "action": "abort" }
    ]
  }
}
```

---

### Phase 6: HITL Checkpoint #2 - QA Approval

#### 6.1 Pause for User Approval

- Update state:
  ```json
  {
    "pipeline": {
      "status": "checkpoint",
      "checkpoint": "qa_approval"
    }
  }
  ```
- Update `sprint-backlog.md`: Pipeline → `⏳ awaiting_qa_approval`

#### 6.2 Display Checkpoint UI

Present to user:

```
═══════════════════════════════════════════════════════════════════
  🛑 HITL CHECKPOINT #2: QA Review Complete
═══════════════════════════════════════════════════════════════════

Story: {story_id} - {story_title}
Gate: {PASS/CONCERNS/FAIL}

🧪 QA FINDINGS:
┌─────────────────────────────────────────────────────────────────┐
│ Tests: ✅ Passing                                               │
│ Coverage: 85%                                                   │
├─────────────────────────────────────────────────────────────────┤
│ ID       │ Severity │ Finding                                   │
├─────────────────────────────────────────────────────────────────┤
│ TEST-001 │ medium   │ Missing integration test for edge case    │
└─────────────────────────────────────────────────────────────────┘

📄 Gate File: {qa_gate_path}

What would you like to do?

  [1] ✅ Approve & Proceed to Commit
  [2] 🔧 Fix Issues First (Dev Agent will address)
  [3] ❌ Abort Pipeline

Enter choice (1/2/3):
```

#### 6.3 Handle User Response

**If Approve (1):**
- Skip Phase 7 (no fixes needed)
- Continue to Phase 8

**If Fix Issues (2):**
- Continue to Phase 7

**If Abort (3):**
- Update state: `failed`
- HALT

---

### Phase 7: QA Remediation (Dev Agent)

#### 7.1 Invoke Dev Agent for Fixes

- Update state: phase → `fixing`
- Update `sprint-backlog.md`: Pipeline → `🔧 fixing`
- Execute task: `.bmad-core/tasks/apply-qa-fixes.md`
- Pass QA findings to Dev Agent
- Dev Agent will:
  - Address each QA issue
  - Re-run tests
  - Update story file

#### 7.2 Verify Fixes

- Wait for Dev Agent completion
- Verify tests pass
- Update state:
  ```json
  {
    "stories": {
      "{story_id}": {
        "state": "awaiting_commit",
        "iterations": 2
      }
    }
  }
  ```

---

### Phase 8: HITL Checkpoint #3 - Commit Approval

#### 8.1 Prepare Commit Data

- Gather all changed files
- Generate commit message based on story
- Update `sprint-backlog.md`: Pipeline → `⏳ awaiting_commit`

#### 8.2 Display Checkpoint UI

Present to user:

```
═══════════════════════════════════════════════════════════════════
  🛑 HITL CHECKPOINT #3: Ready to Commit
═══════════════════════════════════════════════════════════════════

Story: {story_id} - {story_title}

📁 FILES TO COMMIT:
┌─────────────────────────────────────────────────────────────────┐
│ apps/api/src/services/coverage_analyzer.py          (new)       │
│ apps/api/src/routes/coverage.py                     (new)       │
│ apps/api/src/schemas/coverage.py                    (new)       │
│ apps/api/tests/unit/test_coverage.py                (new)       │
│ docs/stories/4.5-coverage-progress-tracking.story.md (modified) │
└─────────────────────────────────────────────────────────────────┘

📝 PROPOSED COMMIT MESSAGE:
feat(4.5): implement coverage progress tracking

- Add CoverageAnalyzer service for mastery/gap/uncertain classification
- Create /api/v1/coverage endpoints
- Add unit and integration tests
- Story status: Done

🤖 Generated with Claude Code

What would you like to do?

  [1] ✅ Commit Changes
  [2] 👀 Review Changes First (show diff)
  [3] ❌ Abort (do not commit)

Enter choice (1/2/3):
```

#### 8.3 Handle User Response

**If Commit (1):**
- Execute git add for listed files
- Execute git commit with message
- Continue to Phase 9

**If Review First (2):**
- Show git diff
- Re-prompt for commit decision

**If Abort (3):**
- Log: "Commit aborted by user. Changes remain uncommitted."
- Update state: paused
- HALT

---

### Phase 9: Completion

#### 9.1 Update Final State

```json
{
  "pipeline": {
    "status": "completed",
    "phase": null,
    "checkpoint": null
  },
  "stories": {
    "{story_id}": {
      "state": "complete",
      "timestamps": { "completed": "{now}" }
    }
  }
}
```

#### 9.2 Update Sprint Backlog

- Update story row: Status → `✅ Complete`, Pipeline → `✅ complete`
- Log to history

#### 9.3 Display Completion Summary

```
═══════════════════════════════════════════════════════════════════
  ✅ PIPELINE COMPLETE
═══════════════════════════════════════════════════════════════════

Story: {story_id} - {story_title}
Duration: {elapsed_time}
Iterations: {iteration_count}

📊 SUMMARY:
  • SM Agent: Drafted story in {time}
  • PO Agent: Validated with {n} amendments
  • Dev Agent: Implemented {n} files
  • QA Agent: Gate {status}

Commit: {commit_hash}

Next story in queue: {next_story_id} - {next_title}
Run /workflow-story-pipeline to continue.
═══════════════════════════════════════════════════════════════════
```

---

## Error Handling

### Agent Failures

If any agent fails:
1. Log error details
2. Update state: `failed`, capture error
3. Update `sprint-backlog.md`: Status → `🚫 Failed`
4. Prompt user with recovery options:
   - Retry current phase
   - Skip to next phase
   - Abort pipeline

### State Recovery

The pipeline supports recovery from any state:
- Read current state from `pipeline-state.json`
- Resume from last checkpoint or phase
- Use `--resume` flag to continue

---

## Configuration

### Timeouts

```yaml
timeouts:
  sm_agent: 300000    # 5 minutes
  po_agent: 300000    # 5 minutes
  dev_agent: 1800000  # 30 minutes
  qa_agent: 600000    # 10 minutes
```

### Feature Flags

```yaml
features:
  auto_commit: false          # Require HITL for commits
  skip_qa_on_pass: false      # Skip HITL #2 if QA passes
  parallel_validation: false  # Run PO validation in parallel with draft
```

---

## Related Tasks

- `.bmad-core/tasks/create-next-story.md` - SM Agent story drafting
- `.bmad-core/tasks/validate-next-story.md` - PO Agent validation
- `.bmad-core/tasks/review-story.md` - QA Agent review
- `.bmad-core/tasks/apply-qa-fixes.md` - Dev Agent QA remediation
- `.bmad-core/tasks/qa-gate.md` - QA gate file creation

## State Files

- `.bmad-core/state/pipeline-state.json` - Machine state
- `.bmad-core/state/pipeline-state-schema.md` - Schema documentation
- `docs/prd/sprint-backlog.md` - Human-readable backlog
