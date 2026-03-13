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

1. Pull the latest notebook state:
   ```bash
   cd ~/codebox/notebook && git pull
   ```
2. Read `~/codebox/notebook/projects/<project>/STATUS.md`. If the project directory does not exist, create it and add a `STATUS.md` file.
3. If you need more context, scan recent files in `sessions/`.
4. If you don't know which project is relevant, read `~/codebox/notebook/PROJECTS.md`.

## Ending a Session

Do all three of these steps before finishing:

### 1. Write a Session Log

Generate a short (max 6-8 words) session description.

Create `~/codebox/notebook/projects/<project>/sessions/YYYY-MM-DD_{session description, formatted as snakecase and all lowercase}.md`.

```markdown
---
title: "{session description}"
date: YYYY-MM-DD
time: "HH:MM"           # session start time (24h, local timezone)
project: <project-name>
tldr: >
  One to two sentences summarizing the session's activities and outcomes.
model: claude-sonnet-4-20250514  # or gpt-4.1, etc.
harness: claude-code    # claude-code | codex | opencode | aider | custom
duration: "Xh Ym"       # wall-clock session duration, if known
tokens: ~               # total tokens used, if available (null otherwise)
git_branch: ~           # branch worked on, if applicable
status: completed       # completed | interrupted | blocked
tags: []                # freeform tags for searchability, e.g. [refactor, auth, bugfix]
---

# YYYY-MM-DD -- {session description}

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
git commit -m "<project>: session log YYYY-MM-DD {session description}"
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
- **Frontmatter**: Every session log must have a YAML frontmatter block. Fill in all fields you have data for; use `~` (null) for anything unavailable. Never fabricate values for `duration` or `tokens` — leave them null if you don't have reliable numbers.
- **Tone**: Write for a technically skilled reader with zero context on this specific session. Concise but not cryptic.
- **Granularity**: Log meaningful work. If a session is trivial ("ran tests, they passed"), a one-line session log is fine.
- **Honesty**: If you're uncertain about something, say so. Never fabricate details to fill the template.
