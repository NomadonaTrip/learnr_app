# HITL Checkpoint Handler

<!-- Powered by BMAD Core -->

## Purpose

Display and handle Human-in-the-Loop (HITL) checkpoints during the story lifecycle pipeline. This task presents checkpoint data to the user and captures their decision.

## Checkpoint Types

| Checkpoint | Trigger | Purpose |
|------------|---------|---------|
| `po_approval` | After PO validation | Approve story before development |
| `qa_approval` | After QA review | Approve QA results, decide on fixes |
| `commit_approval` | After implementation/fixes | Approve and commit changes |

## Inputs

```yaml
required:
  - checkpoint: 'po_approval | qa_approval | commit_approval'
  - state_file: '.bmad-core/state/pipeline-state.json'
```

## Execution

### 1. Load Checkpoint Data

- Read `pipeline-state.json`
- Extract `checkpointData` object
- Validate checkpoint type matches expected

### 2. Display Checkpoint UI

Based on checkpoint type, display appropriate UI:

---

#### PO Approval Checkpoint (HITL #1)

```
═══════════════════════════════════════════════════════════════════════════════
  🛑 HITL CHECKPOINT #1: PO Validation Complete
═══════════════════════════════════════════════════════════════════════════════

📋 STORY: {story_id} - {story_title}

📊 VALIDATION STATUS: {GO/NO-GO} (Score: {score}/10)

📝 PO AMENDMENTS:
╭─────────────────────────────────────────────────────────────────────────────╮
│ # │ Section               │ Change                                          │
├───┼───────────────────────┼─────────────────────────────────────────────────┤
│ 1 │ Acceptance Criteria   │ Added AC for error handling edge case           │
│ 2 │ Dev Notes             │ Added missing API endpoint specification        │
│ 3 │ Tasks                 │ Reordered tasks for logical dependency flow     │
╰─────────────────────────────────────────────────────────────────────────────╯

📄 Story File: {story_file_path}

💡 TIP: Review the story file to verify amendments before approving.

───────────────────────────────────────────────────────────────────────────────
  What would you like to do?
───────────────────────────────────────────────────────────────────────────────

  [1] ✅ APPROVE & Continue to Development
      → Story will be passed to Dev Agent for implementation

  [2] 📝 REQUEST MORE CHANGES
      → Pipeline pauses; you can edit the story manually
      → Run `/workflow-story-pipeline --resume` when ready

  [3] ❌ ABORT Pipeline
      → Story returns to backlog; all progress discarded

───────────────────────────────────────────────────────────────────────────────
```

---

#### QA Approval Checkpoint (HITL #2)

```
═══════════════════════════════════════════════════════════════════════════════
  🛑 HITL CHECKPOINT #2: QA Review Complete
═══════════════════════════════════════════════════════════════════════════════

📋 STORY: {story_id} - {story_title}

🧪 QA GATE: {PASS/CONCERNS/FAIL}

📊 TEST RESULTS:
╭─────────────────────────────────────────────────────────────────────────────╮
│ Tests:     ✅ 12 passing, 0 failing                                         │
│ Coverage:  85% (target: 80%)                                                │
│ Lint:      ✅ No issues                                                     │
╰─────────────────────────────────────────────────────────────────────────────╯

⚠️  QA FINDINGS:
╭─────────────────────────────────────────────────────────────────────────────╮
│ ID       │ Severity │ Finding                          │ Action Required    │
├──────────┼──────────┼──────────────────────────────────┼────────────────────┤
│ TEST-001 │ medium   │ Missing integration test for     │ Add test for empty │
│          │          │ edge case                        │ belief state       │
├──────────┼──────────┼──────────────────────────────────┼────────────────────┤
│ MNT-001  │ low      │ Consider extracting validation   │ Optional refactor  │
│          │          │ to separate class                │                    │
╰─────────────────────────────────────────────────────────────────────────────╯

📄 Gate File: {qa_gate_file_path}

───────────────────────────────────────────────────────────────────────────────
  What would you like to do?
───────────────────────────────────────────────────────────────────────────────

  [1] ✅ APPROVE & Proceed to Commit
      → Accept current state (concerns noted but not blocking)
      → Skip fixes; proceed directly to commit

  [2] 🔧 FIX ISSUES First
      → Dev Agent will address QA findings
      → Pipeline continues after fixes complete

  [3] ❌ ABORT Pipeline
      → Implementation preserved but not committed
      → Story returns to implementing state

───────────────────────────────────────────────────────────────────────────────
```

---

#### Commit Approval Checkpoint (HITL #3)

```
═══════════════════════════════════════════════════════════════════════════════
  🛑 HITL CHECKPOINT #3: Ready to Commit
═══════════════════════════════════════════════════════════════════════════════

📋 STORY: {story_id} - {story_title}

📁 FILES TO COMMIT ({file_count} files):
╭─────────────────────────────────────────────────────────────────────────────╮
│ Status   │ File Path                                                        │
├──────────┼──────────────────────────────────────────────────────────────────┤
│ ✚ new    │ apps/api/src/services/coverage_analyzer.py                       │
│ ✚ new    │ apps/api/src/routes/coverage.py                                  │
│ ✚ new    │ apps/api/src/schemas/coverage.py                                 │
│ ✚ new    │ apps/api/tests/unit/services/test_coverage_analyzer.py           │
│ ✚ new    │ apps/api/tests/integration/test_coverage_api.py                  │
│ ✎ mod    │ docs/stories/4.5-coverage-progress-tracking.story.md             │
│ ✎ mod    │ docs/prd/sprint-backlog.md                                       │
╰─────────────────────────────────────────────────────────────────────────────╯

📝 PROPOSED COMMIT MESSAGE:
╭─────────────────────────────────────────────────────────────────────────────╮
│ feat(4.5): implement coverage progress tracking                             │
│                                                                             │
│ - Add CoverageAnalyzer service for belief state classification              │
│ - Create GET /api/v1/coverage/summary endpoint                              │
│ - Create GET /api/v1/coverage/by-ka endpoint                                │
│ - Add unit tests for CoverageAnalyzer                                       │
│ - Add integration tests for coverage API                                    │
│                                                                             │
│ Story: 4.5 - Coverage Progress Tracking                                     │
│ Status: Done                                                                │
│                                                                             │
│ 🤖 Generated with Claude Code                                               │
│ Co-Authored-By: SM Agent, PO Agent, Dev Agent, QA Agent                     │
╰─────────────────────────────────────────────────────────────────────────────╯

───────────────────────────────────────────────────────────────────────────────
  What would you like to do?
───────────────────────────────────────────────────────────────────────────────

  [1] ✅ COMMIT Changes
      → Execute git commit with proposed message
      → Update story status to Done
      → Pipeline completes

  [2] 👀 REVIEW Changes First
      → Show full git diff
      → Return to this prompt after review

  [3] ✏️  EDIT Commit Message
      → Modify the commit message before committing

  [4] ❌ ABORT (Do Not Commit)
      → Changes remain uncommitted
      → Pipeline pauses; run --resume to return here

───────────────────────────────────────────────────────────────────────────────
```

---

### 3. Capture User Response

Use appropriate input method to capture user choice:

```yaml
response:
  choice: 1-4
  custom_input: null  # For option 3 (edit commit message)
```

### 4. Update State Based on Response

**Approve/Continue:**
```json
{
  "pipeline": {
    "status": "running",
    "checkpoint": null
  }
}
```

**Request Changes/Pause:**
```json
{
  "pipeline": {
    "status": "paused",
    "checkpoint": "{current_checkpoint}"
  }
}
```

**Abort:**
```json
{
  "pipeline": {
    "status": "failed",
    "error": "Aborted by user at {checkpoint}"
  }
}
```

### 5. Return Decision

Return structured decision to orchestrator:

```yaml
decision:
  action: 'continue | pause | fix | abort | review'
  checkpoint: '{checkpoint_type}'
  custom_data: null  # e.g., edited commit message
```

---

## Error Handling

- If state file missing: HALT with "Pipeline state not found"
- If checkpoint data missing: HALT with "Invalid checkpoint state"
- If unexpected response: Re-prompt user

---

## Integration

This task is called by `workflow-story-pipeline.md` at each HITL checkpoint. It should not be invoked directly by users.

## Related Files

- `.bmad-core/state/pipeline-state.json` - State storage
- `.bmad-core/tasks/workflow-story-pipeline.md` - Parent orchestrator
