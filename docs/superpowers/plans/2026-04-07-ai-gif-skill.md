# AI GIF Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an agent-first skill repo that can generate keyed sprite-sheet templates, call Gemini for sprite-sheet generation, remove backgrounds with rembg, assemble GIFs, and ship in a `skills.sh`-compatible layout.

**Architecture:** Keep the repo root as a skills collection and place the installable skill under `skills/ai-gif-skill`. Put reusable Python logic under `skills/ai-gif-skill/src/ai_gif_skill`, expose one agent-first CLI with stage subcommands, and keep per-stage wrapper scripts in `skills/ai-gif-skill/scripts/`. Make stdout JSON the machine contract and keep stderr human-readable.

**Tech Stack:** Python, uv, Pillow, google-genai, rembg, pytest

---

### Task 1: Create the Skill Repo Skeleton

**Files:**
- Create: `skills/ai-gif-skill/SKILL.md`
- Create: `skills/ai-gif-skill/references/cli-contract.md`
- Create: `docs/superpowers/specs/2026-04-07-ai-gif-skill-design.md`
- Create: `docs/superpowers/plans/2026-04-07-ai-gif-skill.md`
- Create: `skills/ai-gif-skill/pyproject.toml`
- Create: `README.md`

- [ ] Step 1: Write the skill metadata and workflow summary under `skills/ai-gif-skill`.
- [ ] Step 2: Save the CLI contract reference file.
- [ ] Step 3: Save the design doc and implementation plan.
- [ ] Step 4: Add project packaging and test config to `pyproject.toml`.

### Task 2: Implement Template and Prompt Logic

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/template.py`
- Create: `skills/ai-gif-skill/src/ai_gif_skill/generate.py`
- Test: `tests/test_template.py`
- Test: `tests/test_prompting.py`

- [ ] Step 1: Write failing tests for template output and prompt rules.
- [ ] Step 2: Run `uv run --extra dev pytest tests/test_template.py tests/test_prompting.py -q` and confirm failure.
- [ ] Step 3: Implement the smallest template and prompt logic that passes.
- [ ] Step 4: Re-run the same tests and confirm success.

### Task 3: Implement Cutout and GIF Logic

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/cutout.py`
- Create: `skills/ai-gif-skill/src/ai_gif_skill/gif.py`
- Test: `tests/test_cutout.py`
- Test: `tests/test_gif.py`

- [ ] Step 1: Write failing tests for cutout output and GIF slicing.
- [ ] Step 2: Run `uv run --extra dev pytest tests/test_cutout.py tests/test_gif.py -q` and confirm failure.
- [ ] Step 3: Implement the smallest cutout and GIF logic that passes.
- [ ] Step 4: Re-run the same tests and confirm success.

### Task 4: Implement the Agent-First CLI Surface

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/cli.py`
- Create: `skills/ai-gif-skill/scripts/template_sheet.py`
- Create: `skills/ai-gif-skill/scripts/generate_with_gemini.py`
- Create: `skills/ai-gif-skill/scripts/cutout_with_rembg.py`
- Create: `skills/ai-gif-skill/scripts/assemble_gif.py`
- Test: `tests/test_cli.py`

- [ ] Step 1: Write the failing CLI integration test.
- [ ] Step 2: Run `uv run --extra dev pytest tests/test_cli.py -q` and confirm failure.
- [ ] Step 3: Implement the minimal subcommand parser and wrappers.
- [ ] Step 4: Re-run the CLI test and confirm success.

### Task 5: Validate the Skill Deliverable

**Files:**
- Create: `skills/ai-gif-skill/agents/openai.yaml`

- [ ] Step 1: Generate `agents/openai.yaml` from the finalized skill text.
- [ ] Step 2: Run `python3 /Users/wangnov/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ai-gif-skill` and confirm the skill validates.
- [ ] Step 3: Run `uv run --project skills/ai-gif-skill --extra dev pytest tests -q` and confirm the full test suite passes.
