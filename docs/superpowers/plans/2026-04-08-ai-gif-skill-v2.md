# AI GIF Skill v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `ai-gif-skill` into a provider-agnostic, stage-oriented media-to-GIF toolkit that supports both `sheet -> gif` and `image -> video -> frames -> gif` workflows while preserving the current v1 commands as compatibility aliases.

**Architecture:** Keep the CLI workflow-oriented and file-based. Separate remote generation providers from local media-processing stages, then layer thin pipeline wrappers on top of those stages. Preserve `generate` and `gif` as legacy aliases, but implement the new surface through explicit commands like `generate-sheet`, `generate-video`, `extract-frames`, and `gif-from-frames`.

**Tech Stack:** Python, uv, Pillow, google-genai, xAI HTTP/SDK integration, rembg, ffmpeg, pytest

---

### Task 1: Introduce the Provider Abstraction and Shared Request Types

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/providers/__init__.py`
- Create: `skills/ai-gif-skill/src/ai_gif_skill/providers/base.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/generate.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/cli.py`
- Test: `tests/test_generate.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing parser and provider-registry tests**

Add tests that prove:

- `generate-sheet` and `generate-image` accept `--provider`
- `generate` still parses as a legacy alias for sheet generation
- unknown providers fail with a clear error

- [ ] **Step 2: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_generate.py tests/test_cli.py -q`

Expected: FAIL because the parser and generation layer do not yet expose provider-aware commands.

- [ ] **Step 3: Add the shared provider contract**

Implement a minimal shared interface in `providers/base.py`, for example:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    output_path: Path
    background: str | None = None


class SheetGenerator(Protocol):
    def generate_sheet(self, *, input_image_path: Path, request: object, model: str | None = None) -> dict[str, object]: ...
```

Keep this layer small. It exists to stabilize dispatch, not to erase every provider difference.

- [ ] **Step 4: Update `cli.py` to register the new command names without implementation detail**

Add parser entries for:

- `generate-sheet`
- `generate-image`

Keep `generate` as an alias path that maps to `generate-sheet`.

- [ ] **Step 5: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_generate.py tests/test_cli.py -q`

Expected: PASS for parser and registry coverage.

- [ ] **Step 6: Commit the abstraction scaffold**

```bash
git add skills/ai-gif-skill/src/ai_gif_skill/providers/__init__.py \
  skills/ai-gif-skill/src/ai_gif_skill/providers/base.py \
  skills/ai-gif-skill/src/ai_gif_skill/generate.py \
  skills/ai-gif-skill/src/ai_gif_skill/cli.py \
  tests/test_generate.py tests/test_cli.py
git commit -m "refactor: add provider abstraction scaffold"
```

### Task 2: Implement Gemini and Grok Image Generation for Sheets and Single Images

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/providers/gemini_image.py`
- Create: `skills/ai-gif-skill/src/ai_gif_skill/providers/grok_image.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/generate.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/layout_metadata.py`
- Test: `tests/test_generate.py`

- [ ] **Step 1: Write failing generation tests for both image providers**

Add tests that prove:

- `generate-sheet --provider gemini` preserves sheet metadata on output
- `generate-sheet --provider grok` preserves sheet metadata on output
- `generate-image --provider gemini` writes one PNG without sheet metadata requirements
- `generate-image --provider grok` writes one PNG without sheet metadata requirements

- [ ] **Step 2: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_generate.py -q`

Expected: FAIL because only Gemini sheet generation exists today.

- [ ] **Step 3: Implement the Gemini image provider**

Move the existing Gemini logic out of `generate.py` into `providers/gemini_image.py`. Keep the current prompt-building logic for sheets, and add a simpler single-image path that does not require sheet metadata.

- [ ] **Step 4: Implement the Grok image provider**

Add Grok-backed image generation with the same normalized file contract:

- sheet mode writes one PNG with carried layout metadata
- single-image mode writes one PNG without fabricated sheet metadata

Return provider-normalized JSON fields rather than raw response payloads.

- [ ] **Step 5: Update the generation orchestration layer**

Make `generate.py` dispatch by provider and mode instead of talking to Gemini directly.

- [ ] **Step 6: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_generate.py -q`

Expected: PASS with both providers mocked.

- [ ] **Step 7: Commit the image-generation layer**

```bash
git add skills/ai-gif-skill/src/ai_gif_skill/providers/gemini_image.py \
  skills/ai-gif-skill/src/ai_gif_skill/providers/grok_image.py \
  skills/ai-gif-skill/src/ai_gif_skill/generate.py \
  skills/ai-gif-skill/src/ai_gif_skill/layout_metadata.py \
  tests/test_generate.py
git commit -m "feat: add provider-backed image generation"
```

### Task 3: Implement Video Generation with Gemini and Grok

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/video.py`
- Create: `skills/ai-gif-skill/src/ai_gif_skill/providers/gemini_video.py`
- Create: `skills/ai-gif-skill/src/ai_gif_skill/providers/grok_video.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/cli.py`
- Test: `tests/test_video.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for `generate-video`**

Add tests that prove:

- `generate-video --provider gemini` accepts prompt, duration, output path, and optional reference image
- `generate-video --provider grok` accepts the same normalized inputs
- asynchronous provider responses are polled and normalized before the command returns
- missing provider credentials fail with stage-specific errors

- [ ] **Step 2: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_video.py tests/test_cli.py -q`

Expected: FAIL because no video stage exists yet.

- [ ] **Step 3: Implement the shared video request model**

In `video.py`, add a thin orchestration layer with a request object like:

```python
@dataclass(frozen=True)
class VideoGenerationRequest:
    prompt: str
    duration_seconds: int
    output_path: Path
    reference_image_path: Path | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
```

- [ ] **Step 4: Implement `providers/gemini_video.py`**

Wrap the Gemini video API in a file-oriented adapter that:

- uploads any reference image if needed
- polls until the operation completes
- downloads the final video to `output_path`
- returns normalized JSON metadata

- [ ] **Step 5: Implement `providers/grok_video.py`**

Wrap the Grok video API in the same normalized contract:

- submit generation
- poll request status
- download final MP4
- preserve provider/model/duration fields in the returned payload

- [ ] **Step 6: Expose `generate-video` from `cli.py`**

Add the parser, validate required flags, and keep all provider-specific details out of the CLI module.

- [ ] **Step 7: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_video.py tests/test_cli.py -q`

Expected: PASS with mocked provider implementations.

- [ ] **Step 8: Commit the video-generation stage**

```bash
git add skills/ai-gif-skill/src/ai_gif_skill/video.py \
  skills/ai-gif-skill/src/ai_gif_skill/providers/gemini_video.py \
  skills/ai-gif-skill/src/ai_gif_skill/providers/grok_video.py \
  skills/ai-gif-skill/src/ai_gif_skill/cli.py \
  tests/test_video.py tests/test_cli.py
git commit -m "feat: add provider-backed video generation"
```

### Task 4: Add Frame Extraction and Frame-Directory Contracts

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/frames.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/cutout.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/cli.py`
- Test: `tests/test_frames.py`
- Test: `tests/test_cutout.py`

- [ ] **Step 1: Write failing tests for frame extraction and manifests**

Add tests that prove:

- `extract-frames` writes a deterministic frame directory
- a `frames_manifest.json` file is written alongside the frames
- manifest fields include `frame_count`, `fps`, `source_path`, `width`, and `height`

- [ ] **Step 2: Write failing tests for directory-wide cutout**

Add tests that prove:

- `cutout-frames` reads an input frame directory
- it writes one output frame directory with matching frame count
- it preserves or updates the frame manifest correctly

- [ ] **Step 3: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_frames.py tests/test_cutout.py -q`

Expected: FAIL because frame-directory stages do not exist yet.

- [ ] **Step 4: Implement `frames.py`**

Add helpers for:

- extracting frames from a video with ffmpeg
- writing and reading `frames_manifest.json`
- validating frame directory completeness

- [ ] **Step 5: Extend `cutout.py` with directory-wide helpers**

Keep the current single-image cutout API intact. Add a separate frame-directory path instead of overloading `run_cutout` with too many modes.

- [ ] **Step 6: Expose `extract-frames` and `cutout-frames` in `cli.py`**

Make each command accept explicit input and output directories.

- [ ] **Step 7: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_frames.py tests/test_cutout.py -q`

Expected: PASS with manifest assertions.

- [ ] **Step 8: Commit the frame-processing stage**

```bash
git add skills/ai-gif-skill/src/ai_gif_skill/frames.py \
  skills/ai-gif-skill/src/ai_gif_skill/cutout.py \
  skills/ai-gif-skill/src/ai_gif_skill/cli.py \
  tests/test_frames.py tests/test_cutout.py
git commit -m "feat: add frame extraction and cutout stages"
```

### Task 5: Extend GIF Assembly to Support Frame Directories

**Files:**
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/gif.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/cli.py`
- Test: `tests/test_gif.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for `gif-from-frames`**

Add tests that prove:

- frame directories are assembled in lexical frame order
- transparent PNG frames remain transparent in the GIF output
- `gif` still behaves as the legacy alias for `gif-from-sheet`

- [ ] **Step 2: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_gif.py tests/test_cli.py -q`

Expected: FAIL because GIF assembly only knows how to slice sheets today.

- [ ] **Step 3: Implement frame-directory GIF assembly**

Add a second explicit entrypoint in `gif.py`, for example:

```python
def assemble_gif_from_frames(*, frames_dir: Path, output_path: Path, duration_ms: int, loop: int) -> dict[str, object]:
    ...
```

Do not remove or weaken the current sheet-based path.

- [ ] **Step 4: Expose `gif-from-sheet`, `gif-from-frames`, and legacy `gif`**

Keep `gif` mapped to the sheet path for backward compatibility.

- [ ] **Step 5: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_gif.py tests/test_cli.py -q`

Expected: PASS for both GIF entrypoints and the legacy alias.

- [ ] **Step 6: Commit the GIF extension**

```bash
git add skills/ai-gif-skill/src/ai_gif_skill/gif.py \
  skills/ai-gif-skill/src/ai_gif_skill/cli.py \
  tests/test_gif.py tests/test_cli.py
git commit -m "feat: add frame-based gif assembly"
```

### Task 6: Add `sheet-pipeline` and `video-pipeline` Wrapper Commands

**Files:**
- Create: `skills/ai-gif-skill/src/ai_gif_skill/pipelines.py`
- Modify: `skills/ai-gif-skill/src/ai_gif_skill/cli.py`
- Test: `tests/test_pipelines.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for `sheet-pipeline`**

Add tests that prove:

- one `--provider` controls the remote generation step
- the command returns a `stages` list and `final_output_path`
- the wrapper calls existing stage helpers rather than duplicating logic

- [ ] **Step 2: Write failing tests for `video-pipeline`**

Add tests that prove:

- `--image-provider` and `--video-provider` can differ
- `--provider` works only as a shorthand for same-provider runs
- the wrapper emits all intermediate artifact paths in order

- [ ] **Step 3: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_pipelines.py tests/test_cli.py -q`

Expected: FAIL because no pipeline wrappers exist yet.

- [ ] **Step 4: Implement `pipelines.py`**

Keep the implementation thin. Each pipeline function should orchestrate already-tested stage helpers and only add minimal glue for path wiring and JSON summary assembly.

- [ ] **Step 5: Expose both pipeline commands from `cli.py`**

Do not hide stage commands or make the pipeline wrappers the only documented surface.

- [ ] **Step 6: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_pipelines.py tests/test_cli.py -q`

Expected: PASS with explicit stage ordering and provider separation.

- [ ] **Step 7: Commit the pipeline layer**

```bash
git add skills/ai-gif-skill/src/ai_gif_skill/pipelines.py \
  skills/ai-gif-skill/src/ai_gif_skill/cli.py \
  tests/test_pipelines.py tests/test_cli.py
git commit -m "feat: add sheet and video pipelines"
```

### Task 7: Update Scripts, Docs, Skill Guidance, and Packaging

**Files:**
- Modify: `skills/ai-gif-skill/SKILL.md`
- Modify: `skills/ai-gif-skill/references/cli-contract.md`
- Modify: `skills/ai-gif-skill/pyproject.toml`
- Modify: `README.md`
- Modify: `skills/ai-gif-skill/scripts/generate_with_gemini.py`
- Modify: `skills/ai-gif-skill/scripts/assemble_gif.py`
- Create: `skills/ai-gif-skill/scripts/generate_image.py`
- Create: `skills/ai-gif-skill/scripts/generate_video.py`
- Create: `skills/ai-gif-skill/scripts/extract_frames.py`
- Create: `skills/ai-gif-skill/scripts/cutout_frames.py`
- Create: `skills/ai-gif-skill/scripts/assemble_gif_from_frames.py`
- Test: `tests/test_repo_layout.py`

- [ ] **Step 1: Write failing docs and layout tests**

Add or update tests that prove:

- the repo layout still satisfies existing skill packaging expectations
- new wrapper scripts exist where the skill documentation points to them

- [ ] **Step 2: Run the focused tests to confirm failure**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_repo_layout.py -q`

Expected: FAIL once the new script expectations are added.

- [ ] **Step 3: Update packaging and scripts**

Add any provider dependencies needed for xAI support. Keep provider imports lazy when practical so a missing provider dependency fails only when that provider is selected.

- [ ] **Step 4: Update the machine and human docs**

Synchronize:

- `SKILL.md`
- `references/cli-contract.md`
- `README.md`

Make sure they all describe:

- stage-first command usage
- the two pipeline wrappers
- provider selection rules
- compatibility aliases

- [ ] **Step 5: Re-run the focused tests and confirm success**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests/test_repo_layout.py -q`

Expected: PASS with updated script and doc references.

- [ ] **Step 6: Commit the docs and wrapper updates**

```bash
git add skills/ai-gif-skill/SKILL.md \
  skills/ai-gif-skill/references/cli-contract.md \
  skills/ai-gif-skill/pyproject.toml \
  README.md \
  skills/ai-gif-skill/scripts/generate_with_gemini.py \
  skills/ai-gif-skill/scripts/assemble_gif.py \
  skills/ai-gif-skill/scripts/generate_image.py \
  skills/ai-gif-skill/scripts/generate_video.py \
  skills/ai-gif-skill/scripts/extract_frames.py \
  skills/ai-gif-skill/scripts/cutout_frames.py \
  skills/ai-gif-skill/scripts/assemble_gif_from_frames.py \
  tests/test_repo_layout.py
git commit -m "docs: update skill guidance for v2 workflows"
```

### Task 8: Regenerate Skill Metadata and Run Full Validation

**Files:**
- Modify: `skills/ai-gif-skill/agents/openai.yaml`

- [ ] **Step 1: Regenerate `agents/openai.yaml` from the final skill text**

Use the same generation approach already used in the repo so the skill metadata stays in sync with `SKILL.md`.

- [ ] **Step 2: Run the skill validator**

Run: `uv run --project skills/ai-gif-skill --with pyyaml python /Users/wangnov/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ai-gif-skill`

Expected: validator exits successfully.

- [ ] **Step 3: Run the full test suite**

Run: `uv run --project skills/ai-gif-skill --extra dev pytest tests -q`

Expected: PASS for all CLI, provider, frame, GIF, pipeline, and repo-layout tests.

- [ ] **Step 4: Run one final smoke pass on the CLI help surface**

Run:

```bash
uv run --project skills/ai-gif-skill ai-gif-skill --help
uv run --project skills/ai-gif-skill ai-gif-skill generate-sheet --help
uv run --project skills/ai-gif-skill ai-gif-skill generate-video --help
uv run --project skills/ai-gif-skill ai-gif-skill video-pipeline --help
```

Expected: each command prints help successfully and exposes the expected flags.

- [ ] **Step 5: Commit the finalized v2 implementation**

```bash
git add skills/ai-gif-skill/agents/openai.yaml
git commit -m "chore: finalize ai gif skill v2"
```
