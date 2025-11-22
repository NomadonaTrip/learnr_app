# Introduction

This document outlines the complete fullstack architecture for **LearnR**, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

**LearnR** is an AI-powered adaptive learning platform that transforms professional certification exam preparation from passive memorization to active, adaptive mastery. The platform targets working professionals (ages 30-45) preparing for CBAP certification through:

- **Adaptive Learning Engine:** Real-time competency tracking using simplified IRT across 6 knowledge areas
- **Complete Learning Loop:** Diagnostic → Adaptive Quiz → Explanations → Post-Session Review → Asynchronous Reading Library → Spaced Repetition
- **AI-Powered Content:** GPT-4 + Llama 3.1 for content generation, semantic search via Qdrant vector database
- **Data-Driven Personalization:** 7-question onboarding, 12-question diagnostic, continuous competency estimation
- **Key Innovation:** "Test Fast, Read Later" - zero-interruption quiz flow with asynchronous BABOK reading recommendations

**Target Outcome:** 80%+ first-time pass rate (vs 60% industry average) with 30% reduction in study time through intelligent content targeting.

**MVP Timeline:** 30-day development → 30-day case study validation (exam Dec 21, 2025) → Go/No-Go decision → Beta launch Q1 2026.

---

### Starter Template or Existing Project

**N/A - Greenfield project**

This is a pure greenfield architecture with no existing starter template or codebase. The PRD specifies a custom technical stack (React + FastAPI + PostgreSQL + Qdrant) with no mentions of starter templates or existing frameworks.

**Decision:** Custom greenfield setup provides complete control and aligns perfectly with the PRD's specified technology stack and 30-day MVP timeline.

---

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-21 | 1.0 | Initial fullstack architecture document created | Winston (Architect Agent) |

---
