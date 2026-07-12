# Multi-Agent Pipeline in Claude Code — Learning Notes

How this repo's story → code → review → test workflow is built. Setup date: 2026-07-12.

## The big picture

```
/pipeline "feature request"
      │
      ▼
Main session = ORCHESTRATOR (.claude/skills/pipeline/SKILL.md)
      │  dispatches subagents one by one, pauses for MY approval after each stage
      │
      ├─► 1. story-writer  → writes docs/stories/S-###-<slug>.md   [GATE: I approve]
      ├─► 2. coder         → implements on branch story/S-###-...  [GATE: I approve]
      ├─► 3. reviewer      → checks diff vs acceptance criteria    [GATE: I approve]
      └─► 4. tester        → pytest tests FROM the criteria        [GATE: final accept]
```

## The pieces

| Piece | Where | What it is |
|-------|-------|------------|
| Orchestrator | `.claude/skills/pipeline/SKILL.md` | A skill = instructions the MAIN session follows. It is the "brain". |
| 4 subagents | `.claude/agents/*.md` | Markdown files: YAML frontmatter (`name`, `description`, `tools`, `model`) + a role prompt. |
| Handoff artifact | `docs/stories/S-###-*.md` | The story file — the ONLY shared state between agents. |
| Template | `docs/stories/TEMPLATE.md` | Story format: user story, acceptance criteria, affected files, notes/findings/results sections. |

## Key concepts I should remember

1. **Subagents share NO memory.** Each runs in an isolated context; only its final
   message returns to the orchestrator. So all state must live in a file on disk
   (the story file). This is the core design constraint of multi-agent systems.
2. **Subagents can't spawn subagents.** That's why the orchestrator must be the main
   session (a skill), not another agent.
3. **Tool restrictions enforce roles better than prompts.** The reviewer has no
   Edit/Write tools → it literally cannot "fix while reviewing". The story-writer
   cannot code. Hard constraints beat polite instructions.
4. **Independent verification.** The tester writes tests from the *acceptance
   criteria*, not from the code — otherwise it just tests what the code happens to do.
5. **Bounded loops.** Reviewer→coder fix rounds are capped at 2, then escalate to the
   human. Uncapped agent loops can ping-pong forever.
6. **Model economics.** Coder inherits the strongest model; story-writer / reviewer /
   tester run on sonnet (cheaper, sufficient).
7. **Human gates** = my existing "don't code until go" rule, automated.

## How to run it

```
/pipeline "add a /version endpoint returning the app version"
```

One story = one branch = one small unit of work. Status line in the story file
(Draft → Approved → In Progress → In Review → Testing → Done) is the resume point if a
session dies.

Full docs: `PROJECT_SETUP.md` §8.6.
