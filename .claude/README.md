# Claude Code Configuration

This directory contains Claude Code integration for the B-MAD method framework.

## Available Slash Commands

### Getting Started

#### `/workflow-init`
**Start here!** Initialize your B-MAD workflow path.

This command will:
- Analyze your project goals
- Determine if it's a new (greenfield) or existing (brownfield) project
- Assess project complexity
- Recommend the right planning track (Quick Flow, BMad Method, or Enterprise)
- Create a workflow status file to track your progress

**When to use**: Before starting any B-MAD workflow, run this first to set up your project path.

### Main B-MAD Interface

#### `/bmad`
Access the full B-MAD Master agent with all workflows and capabilities.

This command provides:
- Complete workflow menu (34+ workflows)
- Access to all B-MAD phases (Analysis, Planning, Solutioning, Implementation)
- Workflow orchestration and guidance
- Project phase recommendations

**When to use**: When you want to explore all B-MAD capabilities or need guidance on what to do next.

### Specialized Workflows

#### `/bmad-prd`
Create a Product Requirement Document (PRD).

This command:
- Guides you through comprehensive PRD creation
- Helps define Functional and Non-Functional Requirements
- Creates Epics and User Stories
- Documents technical assumptions

**When to use**: After workflow-init, when following the BMad Method or Enterprise track.

## Quick Start Guide

1. **Initialize your workflow** (REQUIRED FIRST STEP):
   ```
   /workflow-init
   ```
   This will analyze your project and recommend the right development track.

2. **Access B-MAD workflows**:
   ```
   /bmad
   ```
   This opens the main B-MAD menu with all available workflows.

3. **Create specific documents** (as needed):
   ```
   /bmad-prd          # Create a Product Requirement Document
   ```

## The B-MAD Methodology

B-MAD follows a four-phase approach:

### Phase 1: Analysis
- Brainstorming
- Domain research
- Product brief creation

### Phase 2: Planning
- Product Requirement Documents (PRD)
- Tech Specs (Quick Flow track)
- Epic and Story creation
- UX Design

### Phase 3: Solutioning
- Architecture design
- Security planning
- DevOps strategy
- Test architecture

### Phase 4: Implementation
- Sprint planning
- Story development
- Code review
- Testing and validation

## Planning Tracks

B-MAD adapts to your project size:

- **Quick Flow Track**: Fast implementation for bug fixes and small features (2-3 changes)
- **BMad Method Track**: Full planning for products, platforms, and complex features
- **Enterprise Track**: Extended planning with security, compliance, and DevOps

## File Structure

```
.claude/
├── README.md              # This file
└── commands/
    ├── workflow-init.md   # Initialize B-MAD workflow
    ├── bmad.md           # Main B-MAD Master interface
    └── bmad-prd.md       # PRD creation workflow
```

## Output Location

All B-MAD generated documents will be saved to: `docs/`

This includes:
- PRDs, Tech Specs, Architecture docs
- Epics and User Stories
- Test plans and documentation
- Workflow status tracking

## Getting Help

- Run `/bmad` and select from the numbered menu
- Run `/workflow-init` to get personalized workflow recommendations
- Check `.bmad/bmm/docs/` for detailed documentation
- Read `.bmad/README.md` for B-MAD framework overview

## Customization

The B-MAD configuration is stored in:
`.bmad/core/config.yaml`

You can modify:
- User name (how agents address you)
- Communication language
- Output folder location
- Document language

## Next Steps

1. Run `/workflow-init` to get started
2. Follow the recommended workflow path
3. Use `/bmad` to access additional workflows as needed
4. Save all outputs to `docs/` for tracking
