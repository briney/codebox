---
name: lab-notebook
description: >
  Session logging, project status tracking, and work history for AI-assisted development.
  Use this skill at the end of every coding session to write a session log, update project
  status, and commit changes. Also use when starting a session to orient on a project's
  current state, when creating a new project entry in the notebook, or when asked to
  "log this", "update the notebook", "write up what we did", or "what's the status of
  <project>". Trigger broadly — if the user mentions the notebook, session logs, project
  status, or next steps tracking, this skill applies.
---

# Lab Notebook

The lab notebook lives at `~/codebox/notebook/`. It is a git repository tracking work,
decisions, and plans across all projects.

## Directory Structure

```
notebook/
  PROJECTS.md              # index of all active projects
  projects/
    <project-name>/
      STATUS.md             # current state — the single source of truth
      sessions/
        YYYY-MM-DD.md       # session logs
        YYYY-MM-DD-b.md     # multiple sessions per day get a letter suffix
      ARCHITECTURE.md       # optional: system design, data flow
      DECISIONS.md          # optional: append-only major decisions log
      SETUP.md              # optional: environment, dependencies, credentials notes
      BUGS.md               # optional: known issues tracker
```

## Starting a Session

1. Read `~/codebox/notebook/projects/<project>/STATUS.md`.
2. If you need more context, scan recent files in `sessions/`.
3. If you don't know which project is relevant, read `~/codebox/notebook/PROJECTS.md`.

## Ending a Session

Do all three of these steps before finishing:

### 1. Write a Session Log

Create `~/codebox/notebook/projects/<project>/sessions/YYYY-MM-DD.md`.

If a file for today already exists, use a letter suffix: `YYYY-MM-DD-b.md`, `-c.md`, etc.

```markdown
# Session — YYYY-MM-DD

## Summary
One to three sentences: what was accomplished this session.

## Work Performed
Describe what was done. Reference specific files, functions, commits, or commands.
Be concrete — a future reader with no context should understand what happened and why.

## Key Decisions & Rationale
- **Decision**: [what was decided]
  **Why**: [reasoning, alternatives considered, tradeoffs]

(Repeat for each significant decision. Omit this section entirely if the session
was purely mechanical with no judgment calls.)

## Issues & Blockers
Anything unresolved: errors, unexpected behaviors, open questions.
Include error messages verbatim when relevant.

## Next Steps
Concrete, actionable items. Specific enough that a fresh agent could pick
them up without clarification. Prioritize if possible.
```

### 2. Update STATUS.md

Overwrite `~/codebox/notebook/projects/<project>/STATUS.md` with the current state.
This file must always reflect the latest session. It is the first thing read at the
start of the next session.

```markdown
# <Project Name> — Status

## Current State
What works, what's built, what's deployed. A paragraph or two max.

## Open Questions
Things needing decisions or investigation.

## Next Steps
Ordered list of what to do next. Carry forward from the session log's
next steps, updated as appropriate.

## Recent Context
Brief notes on the last 2–3 sessions — just enough to understand trajectory
without reading every session log.
```

### 3. Commit and Push

```bash
cd ~/codebox/notebook
git add -A
git commit -m "<project>: session log YYYY-MM-DD"
git push
```

If the push fails (e.g., diverged remote), pull with rebase first:

```bash
git pull --rebase && git push
```

## Creating a New Project

```bash
mkdir -p ~/codebox/notebook/projects/<project-name>/sessions
```

Create an initial `STATUS.md` with Current State and Next Steps filled in.
Add a one-line entry to `~/codebox/notebook/PROJECTS.md`:

```markdown
- **<project-name>**: One-line description of what this project is.
```

## Living Documents

Create these at the project root when they'd be useful, not preemptively:

- `ARCHITECTURE.md` — system design, component relationships, data flow
- `DECISIONS.md` — append-only log of major architectural decisions (when session-level logging isn't enough)
- `SETUP.md` — how to get the project running, environment requirements
- `BUGS.md` — known issues being tracked informally

## Conventions

- **Dates**: Always `YYYY-MM-DD`.
- **Project names**: Lowercase, hyphenated (`balm`, `paperlens`, `bio-kinema`).
- **Tone**: Write for a technically skilled reader with zero context on this specific session. Concise but not cryptic.
- **Granularity**: Log meaningful work. If a session is trivial ("ran tests, they passed"), a one-line session log is fine.
- **Honesty**: If you're uncertain about something, say so. Never fabricate details to fill the template.
