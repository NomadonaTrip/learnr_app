# Pipeline State Schema Documentation

## Version: 1.0.0

This document defines the schema for `pipeline-state.json`, the machine-readable state store for the story lifecycle pipeline.

---

## Root Schema

```json
{
  "$schema": "pipeline-state-schema-v1",
  "version": "1.0.0",
  "lastUpdated": "ISO-8601 timestamp",
  "currentStory": "story_id or null",
  "pipeline": { ... },
  "stories": { ... },
  "history": [ ... ]
}
```

---

## Pipeline Object

Tracks the current pipeline execution state.

```json
{
  "pipeline": {
    "status": "idle | running | paused | checkpoint | completed | failed",
    "phase": "drafting | validating | implementing | qa_review | fixing | committing | null",
    "checkpoint": "po_approval | qa_approval | commit_approval | null",
    "checkpointData": { ... },
    "startedAt": "ISO-8601 or null",
    "pausedAt": "ISO-8601 or null",
    "error": "error message or null"
  }
}
```

### Pipeline Status Values

| Status | Description |
|--------|-------------|
| `idle` | No active pipeline execution |
| `running` | Pipeline is executing (agents working) |
| `paused` | Pipeline paused by user |
| `checkpoint` | Waiting at HITL checkpoint |
| `completed` | Pipeline finished successfully |
| `failed` | Pipeline failed with error |

### Pipeline Phase Values

| Phase | Description | Agent |
|-------|-------------|-------|
| `drafting` | Story being drafted | SM Agent |
| `validating` | Story being validated/amended | PO Agent |
| `implementing` | Code being written | Dev Agent |
| `qa_review` | QA review in progress | QA Agent |
| `fixing` | QA issues being addressed | Dev Agent |
| `committing` | Preparing commit | System |

### Checkpoint Values

| Checkpoint | Description | Trigger |
|------------|-------------|---------|
| `po_approval` | HITL #1: After PO validation | PO Agent completes |
| `qa_approval` | HITL #2: After QA review | QA Agent completes |
| `commit_approval` | HITL #3: Before commit | Dev Agent completes fixes |

---

## Checkpoint Data Object

Contains information needed to display at HITL checkpoints.

```json
{
  "checkpointData": {
    "checkpoint": "po_approval | qa_approval | commit_approval",
    "storyId": "4.5",
    "storyTitle": "Coverage Progress Tracking",
    "summary": "Human-readable summary of what happened",
    "amendments": [ ... ],
    "qaFindings": { ... },
    "changesForCommit": [ ... ],
    "options": [
      { "key": "approve", "label": "Approve & Continue", "action": "continue" },
      { "key": "changes", "label": "Request Changes", "action": "pause" },
      { "key": "abort", "label": "Abort Pipeline", "action": "abort" }
    ]
  }
}
```

### Checkpoint-Specific Data

**po_approval:**
```json
{
  "amendments": [
    {
      "section": "Acceptance Criteria",
      "change": "Added AC for error handling",
      "reason": "Missing edge case coverage"
    }
  ],
  "validationScore": 8,
  "validationStatus": "GO | NO-GO"
}
```

**qa_approval:**
```json
{
  "qaFindings": {
    "gate": "PASS | CONCERNS | FAIL",
    "issues": [
      {
        "id": "TEST-001",
        "severity": "medium",
        "finding": "Missing integration test",
        "action": "Add test for error scenario"
      }
    ],
    "testsPass": true,
    "coveragePercent": 85
  }
}
```

**commit_approval:**
```json
{
  "changesForCommit": [
    "apps/api/src/services/coverage_analyzer.py",
    "apps/api/src/routes/coverage.py",
    "apps/api/tests/unit/test_coverage.py"
  ],
  "storyStatus": "Done",
  "commitMessage": "feat(4.5): implement coverage progress tracking"
}
```

---

## Stories Object

Tracks state for each story that has entered the pipeline.

```json
{
  "stories": {
    "4.5": {
      "id": "4.5",
      "title": "Coverage Progress Tracking",
      "epicId": "4",
      "state": "backlog | drafting | validating | approved | implementing | qa_review | fixing | complete",
      "storyFile": "docs/stories/4.5-coverage-progress-tracking.story.md",
      "timestamps": {
        "entered": "ISO-8601",
        "drafted": "ISO-8601 or null",
        "validated": "ISO-8601 or null",
        "approved": "ISO-8601 or null",
        "implemented": "ISO-8601 or null",
        "qaReviewed": "ISO-8601 or null",
        "completed": "ISO-8601 or null"
      },
      "agents": {
        "sm": { "status": "pending | running | complete", "output": "..." },
        "po": { "status": "pending | running | complete", "output": "..." },
        "dev": { "status": "pending | running | complete", "output": "..." },
        "qa": { "status": "pending | running | complete", "output": "..." }
      },
      "qaGate": "PASS | CONCERNS | FAIL | null",
      "qaGateFile": "docs/qa/gates/4.5-coverage-progress-tracking.yml",
      "iterations": 1,
      "error": null
    }
  }
}
```

### Story State Values

| State | Description | Next State |
|-------|-------------|------------|
| `backlog` | In sprint backlog, not started | `drafting` |
| `drafting` | SM Agent creating story | `validating` |
| `validating` | PO Agent reviewing/amending | `approved` (HITL) |
| `approved` | User approved at HITL #1 | `implementing` |
| `implementing` | Dev Agent writing code | `qa_review` |
| `qa_review` | QA Agent reviewing | `fixing` or `complete` (HITL) |
| `fixing` | Dev Agent fixing QA issues | `complete` (HITL) |
| `complete` | Story done and committed | - |

---

## History Array

Tracks pipeline execution history for audit and debugging.

```json
{
  "history": [
    {
      "timestamp": "ISO-8601",
      "storyId": "4.5",
      "event": "pipeline_started | phase_changed | checkpoint_reached | user_approved | user_rejected | error | completed",
      "phase": "drafting",
      "details": "Additional context"
    }
  ]
}
```

### Event Types

| Event | Description |
|-------|-------------|
| `pipeline_started` | Pipeline execution began |
| `phase_changed` | Moved to new phase |
| `checkpoint_reached` | HITL checkpoint activated |
| `user_approved` | User approved at checkpoint |
| `user_rejected` | User requested changes |
| `agent_started` | Agent began work |
| `agent_completed` | Agent finished work |
| `error` | Error occurred |
| `completed` | Pipeline finished |

---

## Example: Full State During QA Checkpoint

```json
{
  "$schema": "pipeline-state-schema-v1",
  "version": "1.0.0",
  "lastUpdated": "2025-12-23T14:30:00Z",
  "currentStory": "4.5",
  "pipeline": {
    "status": "checkpoint",
    "phase": "qa_review",
    "checkpoint": "qa_approval",
    "checkpointData": {
      "checkpoint": "qa_approval",
      "storyId": "4.5",
      "storyTitle": "Coverage Progress Tracking",
      "summary": "QA review complete. 1 medium-severity issue found.",
      "qaFindings": {
        "gate": "CONCERNS",
        "issues": [
          {
            "id": "TEST-001",
            "severity": "medium",
            "finding": "Missing integration test for edge case",
            "action": "Add test for empty belief state scenario"
          }
        ],
        "testsPass": true,
        "coveragePercent": 82
      },
      "options": [
        { "key": "approve", "label": "Approve (Accept Concerns)", "action": "continue" },
        { "key": "fix", "label": "Fix Issues First", "action": "fix" },
        { "key": "abort", "label": "Abort Pipeline", "action": "abort" }
      ]
    },
    "startedAt": "2025-12-23T10:00:00Z",
    "pausedAt": null,
    "error": null
  },
  "stories": {
    "4.5": {
      "id": "4.5",
      "title": "Coverage Progress Tracking",
      "epicId": "4",
      "state": "qa_review",
      "storyFile": "docs/stories/4.5-coverage-progress-tracking.story.md",
      "timestamps": {
        "entered": "2025-12-23T10:00:00Z",
        "drafted": "2025-12-23T10:15:00Z",
        "validated": "2025-12-23T10:45:00Z",
        "approved": "2025-12-23T11:00:00Z",
        "implemented": "2025-12-23T13:30:00Z",
        "qaReviewed": "2025-12-23T14:30:00Z",
        "completed": null
      },
      "agents": {
        "sm": { "status": "complete", "output": "Story drafted successfully" },
        "po": { "status": "complete", "output": "Validated with 2 amendments" },
        "dev": { "status": "complete", "output": "Implementation complete, tests passing" },
        "qa": { "status": "complete", "output": "Gate: CONCERNS - 1 medium issue" }
      },
      "qaGate": "CONCERNS",
      "qaGateFile": "docs/qa/gates/4.5-coverage-progress-tracking.yml",
      "iterations": 1,
      "error": null
    }
  },
  "history": [
    { "timestamp": "2025-12-23T10:00:00Z", "storyId": "4.5", "event": "pipeline_started", "phase": null, "details": "Starting pipeline for story 4.5" },
    { "timestamp": "2025-12-23T10:00:00Z", "storyId": "4.5", "event": "phase_changed", "phase": "drafting", "details": "SM Agent drafting story" },
    { "timestamp": "2025-12-23T10:15:00Z", "storyId": "4.5", "event": "agent_completed", "phase": "drafting", "details": "SM Agent completed" },
    { "timestamp": "2025-12-23T10:15:00Z", "storyId": "4.5", "event": "phase_changed", "phase": "validating", "details": "PO Agent validating story" },
    { "timestamp": "2025-12-23T10:45:00Z", "storyId": "4.5", "event": "agent_completed", "phase": "validating", "details": "PO Agent completed with 2 amendments" },
    { "timestamp": "2025-12-23T10:45:00Z", "storyId": "4.5", "event": "checkpoint_reached", "phase": "validating", "details": "HITL #1: PO Approval" },
    { "timestamp": "2025-12-23T11:00:00Z", "storyId": "4.5", "event": "user_approved", "phase": "validating", "details": "User approved story" },
    { "timestamp": "2025-12-23T11:00:00Z", "storyId": "4.5", "event": "phase_changed", "phase": "implementing", "details": "Dev Agent implementing" },
    { "timestamp": "2025-12-23T13:30:00Z", "storyId": "4.5", "event": "agent_completed", "phase": "implementing", "details": "Dev Agent completed" },
    { "timestamp": "2025-12-23T13:30:00Z", "storyId": "4.5", "event": "phase_changed", "phase": "qa_review", "details": "QA Agent reviewing" },
    { "timestamp": "2025-12-23T14:30:00Z", "storyId": "4.5", "event": "agent_completed", "phase": "qa_review", "details": "QA Agent completed: CONCERNS" },
    { "timestamp": "2025-12-23T14:30:00Z", "storyId": "4.5", "event": "checkpoint_reached", "phase": "qa_review", "details": "HITL #2: QA Approval" }
  ]
}
```

---

## State File Operations

### Read State
```bash
cat .bmad-core/state/pipeline-state.json
```

### Update State (via orchestrator)
The orchestrator task handles all state updates. Manual edits should be avoided.

### Reset State
To reset the pipeline:
```json
{
  "pipeline": { "status": "idle", "phase": null, "checkpoint": null },
  "currentStory": null
}
```

---

## Integration with sprint-backlog.md

The `sprint-backlog.md` file is the human-readable view. It should be updated alongside `pipeline-state.json`:

| JSON State | Backlog Status |
|------------|----------------|
| `backlog` | 📋 Ready |
| `drafting` | 📝 Drafting |
| `validating` | 🔍 Validating |
| `approved` | ✅ Approved |
| `implementing` | 💻 Implementing |
| `qa_review` | 🧪 QA Review |
| `fixing` | 🔧 Fixing |
| `complete` | ✅ Complete |
