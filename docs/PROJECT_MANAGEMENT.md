# PRLifts — Project Management

**Version:** 1.0
**Last updated:** April 2026
**Audience:** All team members (human and Claude Code)

> This document defines how PRLifts is built. Every team member —
> human or AI — follows this process. If something is not in this
> document, raise it before assuming.

---

## Table of Contents

1. [Sprint Structure](#1-sprint-structure)
2. [Teams](#2-teams)
3. [Embedded Concerns](#3-embedded-concerns)
4. [User Story Template](#4-user-story-template)
5. [Definition of Done](#5-definition-of-done)
6. [Label Taxonomy](#6-label-taxonomy)
7. [GitHub Projects Board Structure](#7-github-projects-board-structure)
8. [Design Sprint Rule](#8-design-sprint-rule)
9. [Sprint Ceremonies](#9-sprint-ceremonies)
10. [Blocking Conditions](#10-blocking-conditions)
11. [Claude Code Workflow](#11-claude-code-workflow)

---

## 1. Sprint Structure

**Cadence:** One week per sprint.

**Goal:** Every sprint ends with potentially shippable code. "Potentially
shippable" means all stories in the sprint are complete per the Definition
of Done, all tests pass, and the CI pipeline is green. It does not mean
the feature is user-visible — early sprints produce backend and core
library work that is complete but not yet surfaced in UI.

**Sprint numbering:** Sprint 1, Sprint 2, Sprint 3... no resets between
phases. Sprints are continuous across V1 through V4.

**Sprint scope:** Defined at the start of each sprint by moving stories
from Backlog into the current sprint iteration. Scope is fixed once the
sprint starts — new work goes into Backlog, not the current sprint.

**True end-to-end shippable:** A user can run the app and use a feature
end-to-end. Expected from Sprint 4-5 when the first complete vertical
slice (auth + workout logging + PR detection) is implemented.

---

## 2. Teams

Four active development teams. Every story is assigned to exactly one team.

### Backend Team
**Owns:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, APScheduler,
AI integrations (Claude API, Fal.ai), Upstash Redis, Supabase backend.

**Delivers:** API endpoints, database migrations, background jobs,
AI feature implementations, rate limiting, push notification delivery.

### iOS Team
**Owns:** Swift, SwiftUI, SwiftData, Core Library (Swift Package),
TrustKit, PostHog iOS SDK, Sentry iOS SDK.

**Delivers:** iOS app, Core Library models, offline sync engine,
UI screens, push notification handling, deep link routing.

### Infrastructure Team
**Owns:** GitHub Actions, Xcode Cloud, Railway configuration, Supabase
configuration, environment parity, secrets management, CI/CD pipelines.

**Delivers:** CI pipeline changes, environment setup, migration tooling,
deployment configuration, monitoring setup.

### UX/Design Team
**Owns:** Screen specifications, wireframes, interactive prototypes, design system,
copy review, accessibility review, empty states, error states.

**Primary tool:** Claude Design (claude.ai/design) — powered by Claude Opus 4.7.
All wireframes, mockups, and interactive prototypes are produced in Claude Design.
Claude Design reads the repo directly (DESIGN_TOKENS.md, SCREEN_INVENTORY.md,
USER_FLOWS.md) to build a design system automatically. No Figma required.

**Delivers:** Interactive prototypes with Claude Code handoff bundle one sprint ahead
of iOS implementation. Copy for all user-facing strings. Design token updates.
Accessibility audit. The Claude Design handoff bundle is the authoritative design
spec — not a separate document.

**Workflow:**
1. Open claude.ai/design
2. Point Claude Design at the repo — it reads DESIGN_TOKENS.md, SCREEN_INVENTORY.md,
   USER_FLOWS.md automatically
3. Describe the screen — Claude Design produces a prototype
4. Iterate with Siraaj's feedback conversationally
5. Mark design approved in the GitHub Issue
6. Hand off to Claude Code via Claude Design's built-in handoff bundle
7. Claude Code receives design intent directly — no manual translation

---

## 3. Embedded Concerns

These are not separate teams. They embed into every team and every story.

### QA
- Every story has acceptance criteria in Given/When/Then format
- Tests are written as part of implementation, not after
- A story is not Done until tests are written and passing at 90% coverage
- Claude Code writes tests alongside implementation code — never separately
- QA label applied to stories with complex testing requirements

### Security
- Security review checklist runs on every story touching user data
- Stories touching auth, biometric data, AI operations, or payments
  get the `security` label
- Security checklist must be completed before the story moves to Done
- See STANDARDS.md Section 2.6 for the full security review checklist

### DevOps
- Front-loaded into Infrastructure team in sprints 1-3
- After sprint 3, DevOps concerns surface as labels on specific stories
- `devops` label applied to stories touching CI, deployment, or environments
- Every infrastructure change documented in docs/INFRASTRUCTURE_CHANGES.md

### Legal/Compliance
- `legal-blocked` label on any story that cannot start until a legal
  prerequisite is resolved
- Current legal blockers tracked in ARCHITECTURE.md pre-launch checklist
- Future self feature stories are all `legal-blocked` until Fal.ai DPA
  is executed and BIPA consent flow is attorney-reviewed

### AI/ML
- `ai-ml` label on stories touching Claude API, Fal.ai, prompt templates,
  or quality gate
- Prompt evaluation test suite must pass before any prompt template
  is activated
- Body image prompt evaluation is a blocking CI gate
- AI cost estimate reviewed at the end of every sprint containing AI work

---

## 4. User Story Template

Every GitHub Issue follows this template exactly.

```
## User Story

**As a** [type of user]
**I want to** [action]
**So that** [benefit]

## Acceptance Criteria

Given [initial state]
When [action occurs]
Then [expected outcome]
And [additional outcomes]

(repeat Given/When/Then for each scenario)

## Technical Notes

[Any implementation guidance, constraints, or references to architecture
decisions. Link to relevant sections of ARCHITECTURE.md or STANDARDS.md.]

## Dependencies

[Any stories that must be completed before this one can start.]

## Team

[Backend | iOS | Infrastructure | UX/Design]

## Labels

[Select all that apply — see Label Taxonomy]

## Definition of Done

- [ ] Acceptance criteria all satisfied
- [ ] Tests written and passing
- [ ] Coverage at or above 90% for changed code
- [ ] No new linting violations
- [ ] All public functions have docstrings/doc comments
- [ ] No TODO/FIXME without a GitHub issue number
- [ ] No commented-out code
- [ ] PR description explains what changed and why
- [ ] ARCHITECTURE.md updated if any architectural decision was made
- [ ] Security checklist completed (if `security` label)
- [ ] Design spec approved (if UI story)
- [ ] Legal prerequisites met (if `legal-blocked` label)
```

---

## 5. Definition of Done

A story is Done only when ALL of the following are true. This list is
non-negotiable — partial completion is not Done.

**Code quality:**
- [ ] All acceptance criteria satisfied and verified
- [ ] Tests written and passing (unit + integration where applicable)
- [ ] Coverage at or above 90% for changed code
- [ ] No new SwiftLint violations (iOS) or Ruff violations (Backend)
- [ ] No mypy type errors (Backend)
- [ ] No function over 40 lines of implementation logic
- [ ] All public functions have docstrings/doc comments
- [ ] No TODO/FIXME without a GitHub issue number
- [ ] No commented-out code

**Process:**
- [ ] PR opened against main from a feature branch
- [ ] PR description explains what changed and why
- [ ] All PR conversations resolved
- [ ] CI pipeline green (all checks passing)
- [ ] ARCHITECTURE.md updated if any architectural decision was made
- [ ] Merged via squash commit with a clear commit message

**Conditional:**
- [ ] Security review checklist completed (stories with `security` label)
- [ ] Design spec approved before implementation started (iOS UI stories)
- [ ] Legal prerequisites confirmed met (stories with `legal-blocked` label)
- [ ] Prompt evaluation suite passed (stories with `ai-ml` label)
- [ ] Data minimisation question answered in PR (stories adding new data)
- [ ] If story changes any `[iOS]` annotated column: Alembic migration, SwiftData model, and SCHEMA.md all updated in the same PR
- [ ] **iOS PRs:** UI tests must pass locally on iPhone SE via the pre-commit hook before opening the PR. `git commit --no-verify` is never permitted without explicit justification documented in the PR description.

---

## 6. Label Taxonomy

Every story gets a **team label** and one or more **type/concern labels**.

### Team Labels
| Label | Colour | Meaning |
|---|---|---|
| `team-backend` | Blue | Backend team story |
| `team-ios` | Green | iOS team story |
| `team-infrastructure` | Orange | Infrastructure team story |
| `team-ux` | Purple | UX/Design team story |

### Type Labels
| Label | Colour | Meaning |
|---|---|---|
| `feature` | Teal | New user-facing feature |
| `chore` | Grey | Technical work, no user-facing change |
| `bug` | Red | Something broken |
| `debt` | Yellow | Technical debt paydown |
| `spike` | White | Research or investigation, no deliverable code |

### Concern Labels
| Label | Colour | Meaning |
|---|---|---|
| `security` | Dark Red | Security review checklist required |
| `qa` | Dark Blue | Complex testing requirements |
| `devops` | Dark Orange | CI, deployment, or environment changes |
| `legal-blocked` | Dark Yellow | Cannot start until legal prerequisite resolved |
| `ai-ml` | Dark Purple | Touches AI provider, prompt template, or quality gate |
| `design-required` | Pink | Cannot start until design spec is approved |

### Severity Labels (bugs only)
| Label | Colour | Meaning |
|---|---|---|
| `sev-1-critical` | Bright Red | Data loss, security breach, app unusable |
| `sev-2-high` | Orange | Core feature broken, no workaround |
| `sev-3-medium` | Yellow | Feature degraded, workaround exists |
| `sev-4-low` | Light Grey | Minor, cosmetic, edge case |

### Version Labels
| Label | Colour | Meaning |
|---|---|---|
| `v1` | Dark Green | Ships in V1 |
| `v2` | Medium Green | Ships in V2 |
| `v3` | Light Green | Ships in V3 |
| `v4` | Lightest Green | Ships in V4 |

---

## 7. GitHub Projects Board Structure

**Board name:** PRLifts Development

**Type:** Scrum sprint board with iterations

### Columns
| Column | Meaning |
|---|---|
| **Backlog** | All stories not yet assigned to a sprint |
| **Sprint Backlog** | Stories committed to the current sprint |
| **In Progress** | Actively being worked on |
| **In Review** | PR open, awaiting merge |
| **Done** | Merged, verified, Definition of Done complete |

### Views
- **Current Sprint** — filtered to current iteration, grouped by team
- **Backlog** — all unassigned stories, sorted by priority
- **By Team** — all stories grouped by team label
- **By Version** — all stories grouped by version label
- **Blocked** — all stories with `legal-blocked` label

### Fields
Every story has these fields set before it enters a sprint:
- **Title** — user story summary
- **Team** — Backend | iOS | Infrastructure | UX/Design
- **Sprint** — which iteration
- **Priority** — P1 (must have) | P2 (should have) | P3 (nice to have)
- **Version** — V1 | V2 | V3 | V4
- **Story Points** — 1 (trivial) | 2 (small) | 3 (medium) | 5 (large) | 8 (very large, consider splitting)

---

## 8. Design Sprint Rule

UX/Design team runs **one sprint ahead** of iOS implementation.
All design work is produced in **Claude Design** (claude.ai/design).

| Sprint N | UX/Design delivers | Sprint N+1 | iOS builds |
|---|---|---|---|
| Sprint 1 | Onboarding screens 1-4 prototype + handoff bundle | Sprint 2 | Onboarding UI |
| Sprint 2 | Workout logging, Home screen prototype + handoff bundle | Sprint 3 | Workout logging UI |
| Sprint 3 | PR celebration, Future self prototype + handoff bundle | Sprint 4 | PR celebration, Future self UI |

**Rules:**
- iOS never starts building a screen without an approved Claude Design handoff bundle
- Approval means: prototype reviewed by Siraaj, feedback incorporated, explicitly
  marked approved in the GitHub issue
- If a handoff bundle is not ready at sprint start, the iOS story moves to the next
  sprint — it does not start without a bundle
- Claude Design handoff bundles are linked from the corresponding iOS implementation
  story in GitHub Issues
- Claude Design reads DESIGN_TOKENS.md, SCREEN_INVENTORY.md, and USER_FLOWS.md
  from the repo at the start of every design session — these are the source of truth

---

## 9. Sprint Ceremonies

Adapted for a solo developer working with Claude Code.

### Sprint Planning (Monday, ~30 minutes)
- Review backlog
- Select stories for the sprint
- Confirm each story has acceptance criteria before it enters the sprint
- Confirm design specs are ready for any iOS UI stories
- Confirm legal blockers are resolved for any blocked stories

### Daily Check-in (async, 5 minutes)
- Review what was completed yesterday
- Review what is in progress today
- Flag any blockers immediately — don't wait for end of sprint

### Sprint Review (Friday, ~15 minutes)
- Walk through every completed story
- Verify potentially shippable increment is actually shippable
- Demo any user-visible features
- Note anything that didn't complete and why

### Sprint Retrospective (Friday, after review, ~15 minutes)
- What went well
- What didn't go well
- One specific improvement for next sprint
- Record in docs/INCIDENT_LOG.md under "Sprint Retros" section

---

## 10. Blocking Conditions

These stories cannot enter a sprint until their prerequisite is resolved.

### Legal Blockers (current)
| Story | Blocker | Resolution |
|---|---|---|
| Future self image generation | Fal.ai DPA not executed | Execute DPA — start conversation initiated April 2026 |
| BIPA consent flow | Attorney review required | Send Privacy Policy draft for review |
| Future self UI | Legal blockers above | Resolved when DPA + attorney review complete |

### Technical Blockers (sequencing)
| Story | Blocker |
|---|---|
| iOS UI screens | Design spec approved |
| AI features | Backend job infrastructure complete |
| Push notifications | APNs certificates configured |
| Xcode Cloud setup | Xcode project exists |
| Status checks in branch protection | GitHub Actions checks named and running |

---

## 11. Claude Code Workflow

Claude Code is a team member. It works within the same sprint structure
as any human developer. These rules apply to every Claude Code session.

### Session Start
1. Read CLAUDE.md — full briefing, no skipping
2. Read the assigned story — acceptance criteria, technical notes, dependencies
3. Read any linked documents (ARCHITECTURE.md sections, STANDARDS.md sections)
4. Confirm understanding before writing any code

### During Implementation
- Work on one story at a time — never combine stories
- Write tests alongside implementation, not after
- Follow STANDARDS.md for all code — no exceptions
- Use terminology from GLOSSARY.md — no synonyms
- If an architectural decision is needed, stop and flag it — don't invent answers
- If a prerequisite story is not complete, stop and flag it — don't work around it

### Session End
- All acceptance criteria satisfied
- All tests written and passing
- PR opened with clear description
- Definition of Done checklist complete
- ARCHITECTURE.md updated if any decision was made

### What Claude Code Does Not Do
- Make product decisions — flag and ask
- Make visual design decisions without an approved spec
- Merge its own PRs — human reviews and merges
- Activate prompt templates — human approves
- Add new dependencies without flagging — document the reason

