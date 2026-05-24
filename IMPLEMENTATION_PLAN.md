# Implementation Plan: Project Gappy v2 (Spec Alignment)

**Branch:** `refactor/gappy-v2`  
**Status:** In Progress  
**Last Updated:** 2026-05-24

---

## Overview

This plan outlines the work required to align the current Project Gappy codebase with the full Technical Specification (Parts 1 & 2).

All work on this initiative will be done on the `refactor/gappy-v2` branch.

---

## Phase 0: Backup & Branching (Completed)

- [x] Full codebase backup committed to `main`
- [x] New branch `refactor/gappy-v2` created for all spec alignment work
- [x] GitHub remote updated

---

## Phase 1: Foundation (Data Models + Infrastructure)

**Goal:** Align data layer and infrastructure with the specification.

### Key Tasks
- Migrate from SQLite → PostgreSQL + PGVector
- Fully implement `Requirement` model (`obligation_type`, `severity`, `citations`, `source_section`)
- Enhance `Finding` model with:
  - `evidence`, `citations`, `confidence_score`, `undo_until`, `workflow_state`
  - Structured `comment_history`
- Implement proper `User` model with RBAC (`role`, `department`)
- Set up Celery + Redis for background tasks (re-analysis, undo expiration, etc.)

**Priority:** Critical  
**Estimated Effort:** High

---

## Phase 2: Analysis Engine Overhaul

**Goal:** Replace the current fragile LLM-based analysis with the 6-stage pipeline defined in the spec.

### Key Tasks
- Implement **Hybrid Retrieval** (BM25 + Vector + Reranker)
- Build **Evidence Anchoring** (quote + location from SOP)
- Add **Citation Validation** layer with penalty scoring
- Implement proper **Multi-factor Confidence Scoring**
- Refactor `run_gap_analysis()` to follow the full 6-stage pipeline
- Improve requirement extraction reliability

**Priority:** Very High  
**Estimated Effort:** Very High

---

## Phase 3: Workflow & RBAC Engine

**Goal:** Implement the strict compliance officer workflow.

### Key Tasks
- Build workflow state machine (`PENDING_OFFICER` → `PENDING_SUPERVISOR` → `FINAL`)
- Implement **30-minute undo window** (`undo_until` + Celery expiration task)
- Add **Clarification flow** (trigger re-analysis on Clarification)
- Enforce RBAC at both API and template levels
- Add comprehensive audit logging for all finding actions

**Priority:** High  
**Estimated Effort:** High

---

## Phase 4: API & Export Endpoints

### Key Tasks
- Implement missing endpoints:
  - `POST /findings/{id}/undo`
  - `POST /findings/{id}/clarify`
  - Export endpoints (`/analyses/{id}/export/pdf`, `/csv`, `/json`)
- Add proper validation on review endpoints

**Priority:** Medium  
**Estimated Effort:** Medium

---

## Phase 5: Frontend Improvements

### Key Tasks
- Create reusable `FindingCard` component
- Redesign Gap Analysis Report page (reduce density, improve readability)
- Add proper loading states and progress indicators
- Enhance Analysis History selector
- Make UI role-aware

**Priority:** Medium  
**Estimated Effort:** Medium

---

## Phase 6: Testing & Hardening

- Add unit + integration tests for the analysis pipeline
- Add workflow state transition tests
- Performance testing with large document sets
- Improve error handling and retry mechanisms

**Priority:** Medium  
**Estimated Effort:** Medium

---

## Execution Order Recommendation

| Phase | Focus Area                    | Priority | Risk if Skipped          |
|-------|-------------------------------|----------|--------------------------|
| 1     | Data Models + Infrastructure  | Critical | Everything else unstable |
| 2     | Analysis Engine               | Very High| Poor accuracy persists   |
| 3     | Workflow & RBAC               | High     | Compliance requirements unmet |
| 4     | API Endpoints                 | Medium   | Feature incomplete       |
| 5     | Frontend                      | Medium   | User experience suffers  |
| 6     | Testing                       | Medium   | Technical debt           |

---

## Branch Strategy

- All work will be done on `refactor/gappy-v2`
- `main` will remain stable and only receive merges after major milestones
- Regular pushes to remote branch for backup

---

## Next Steps

1. Confirm Phase 1 start (Data Models + PostgreSQL migration)
2. Begin implementation on `refactor/gappy-v2`

