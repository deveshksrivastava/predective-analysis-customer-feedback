---
name: pipeline
description: Use when the user wants a feature built via the multi-agent workflow (story → code → review → test), e.g. "/pipeline add X", "run the pipeline", "build this as a story". Orchestrates the story-writer, coder, reviewer and tester subagents with a user-approval gate after every stage.
---

# /pipeline — story → code → review → test

You are the orchestrator. You run in the main session, dispatch the four subagents with
the Agent tool, and STOP AT EVERY GATE for user approval (AskUserQuestion or plain
question). Never skip a gate. All shared state lives in the story file — always pass its
path to every subagent, because subagents share no memory with you or each other.

Argument: the feature request. If missing, ask what to build.

## Stage 0 — setup

1. Determine the next story ID: highest `S-###` in `docs/stories/` + 1 (first is S-001).
2. Make a short slug from the request. Story file: `docs/stories/S-###-<slug>.md`.
3. Ensure the working tree is clean; if not, stop and ask the user.

## Stage 1 — story

1. Dispatch **story-writer** (Agent tool, subagent_type `story-writer`) with: the feature
   request, the story file path, and the story ID.
2. Show the user the story (user story + acceptance criteria + out of scope).
3. **GATE 1:** approve / edit / reject. On edits, update the story file yourself. On
   approval set `Status: Approved`.

## Stage 2 — code

1. Create and switch to branch `story/S-###-<slug>` (from the current branch). Write the
   branch name into the story's `Branch:` line and set `Status: In Progress`.
2. Dispatch **coder** with the story file path.
3. Show the user the coder's summary plus `git diff --stat` of the branch.
4. **GATE 2:** approve / send back with instructions (re-dispatch coder) / abort.

## Stage 3 — review

1. Set `Status: In Review`. Dispatch **reviewer** with the story file path.
2. Record the reviewer's findings under `## Review findings` in the story file (the
   reviewer is read-only and cannot write them itself).
3. If verdict is `NEEDS FIXES`: dispatch **coder** in fix mode with the Blocker list.
   Then re-dispatch **reviewer**. **Maximum 2 fix rounds** — if blockers remain after
   round 2, stop and put the decision to the user.
4. Show the user the per-AC verdicts and findings.
5. **GATE 3:** accept review outcome / another fix round / abort.

## Stage 4 — test

1. Set `Status: Testing`. Dispatch **tester** with the story file path.
2. Record the per-AC results under `## Test results` in the story file if the tester
   could not.
3. If tests exposed an implementation bug: one coder fix round, then re-run tester
   (same max-2 discipline as review).
4. Show the user the per-AC pass/fail table and pytest summary.
5. **GATE 4 (final):** accept / send back / abort.

## Stage 5 — close

On final acceptance:

1. Set `Status: Done`, tick the AC checkboxes, commit the story file on the branch.
2. Add one row to the decisions-log table in `PROJECT_SETUP.md` §8.5 (date, story ID +
   title, outcome).
3. Tell the user the branch name and suggest next steps (merge / PR / next story). Do
   not merge or push yourself unless asked.

## Rules

- One story per pipeline run. If the story-writer proposes follow-up stories, list them
  for the user at the end.
- If a subagent fails or returns something unusable, retry once with a clearer prompt;
  after that, surface the problem to the user instead of improvising.
- Aborting at any gate: leave the branch and story file in place, set
  `Status: Draft` (or leave as-is), and summarise the state so the run can resume later —
  the story file's `Status:` line is the resume point.
- Keep every user-facing summary short: what happened, what's next, what you need.
