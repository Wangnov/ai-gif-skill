# AI GIF Skill v2 Design

**Goal:** Evolve `ai-gif-skill` from a single-provider sprite-sheet workflow into a provider-agnostic media-to-GIF toolkit that supports both sheet-first and video-first pipelines without breaking the current v1 commands.

## Purpose

Keep the CLI agent-first and stage-oriented, but expand it so the same local post-processing steps can be used with multiple generation providers and multiple media paths:

1. `sheet -> cutout -> gif`
2. `single image -> video -> extract frames -> cutout frames -> gif`

The design should let Gemini and Grok participate independently at the generation stage while keeping the local media-processing chain stable and reusable.

## Current State

The current repository provides a clean v1 workflow:

1. `template`
2. `generate` (Gemini sprite-sheet generation only)
3. `cutout`
4. `gif`

Strengths in the current design:

- stable JSON command outputs
- explicit file-based stage boundaries
- embedded layout metadata for sheet validation
- no hidden daemon or session state

Current limitations:

- `generate` is tightly coupled to Gemini image generation
- there is no provider abstraction
- there is no single-image generation step
- there is no video generation step
- there is no frame extraction step
- `gif` only accepts sheets, not frame directories

## Classification

- Primary role: Workflow / Orchestration
- Primary user type: Agent-Primary
- Primary interaction form: Batch CLI
- Statefulness: Config-Stateful
- Risk profile: Mixed
- Secondary surfaces: human-readable stderr, installable skill guidance, compatibility aliases for existing stage commands
- Confidence level: High
- Hybrid notes: Some subcommands are generation capabilities, but the CLI identity is still orchestrating explicit multi-stage media workflows rather than acting like a general model playground.
- Evolution trajectory: Keep the current workflow-oriented identity and broaden supported generation providers and stage compositions.

## Classification Reasoning

This should remain a workflow CLI rather than becoming a generic media capability CLI. The user’s main need is not “talk to Grok” or “talk to Gemini” in isolation; it is “produce a GIF asset through a reliable chain of discrete media stages.” The provider is an interchangeable step inside a larger workflow. That makes provider selection a secondary concern, not the primary command shape.

The interaction form remains batch CLI because each stage is still best expressed as a direct file-in/file-out command with stable JSON output. There is no need for sessions, a TUI, or a long-running runtime surface.

## Primary Design Stance

Optimize for explicit stage boundaries, interchangeable providers, and reusable local media-processing steps. The CLI should make it easy for an agent to swap only the generation stage while keeping the rest of the chain identical.

This CLI is not trying to become a general-purpose image/video lab, a conversation wrapper over model APIs, or a one-command black box that hides every intermediate artifact. v2 should make more workflows possible without losing the inspectable, retryable nature of v1.

## Command Structure

### Design Principle

Keep stage-by-stage commands as the primary surface. Add high-level pipeline commands as thin wrappers over those stages, not as a replacement for them.

### Recommended Command Shape

Keep existing commands for compatibility:

- `template`
- `cutout`

Promote the generation and GIF commands into more explicit stage names:

- `generate-sheet`
- `generate-image`
- `generate-video`
- `extract-frames`
- `cutout-frames`
- `gif-from-sheet`
- `gif-from-frames`

Add two high-level pipeline wrappers:

- `sheet-pipeline`
- `video-pipeline`

Compatibility aliases:

- `generate` remains as a compatibility alias for `generate-sheet`
- `gif` remains as a compatibility alias for `gif-from-sheet`

### Expected Command Signatures

The command tree should make the stage intent obvious from the required inputs:

- `generate-sheet`: requires an input template image and writes one output sheet PNG
- `generate-image`: takes prompt-driven image generation inputs and writes one output PNG
- `generate-video`: takes a prompt plus an optional reference image or input video, and writes one output MP4
- `extract-frames`: takes one input video and writes one output frame directory plus manifest
- `cutout-frames`: takes one input frame directory and writes one output frame directory plus manifest
- `gif-from-sheet`: takes one input sheet PNG and writes one output GIF
- `gif-from-frames`: takes one input frame directory and writes one output GIF

Provider flag policy:

- stage commands with one generation step use `--provider`
- `sheet-pipeline` may use a single `--provider` because it has one remote generation step
- `video-pipeline` should support `--image-provider` and `--video-provider` separately because mixed-provider chains are a first-class use case
- `video-pipeline` may offer `--provider` only as a shorthand when both generation steps intentionally use the same provider

### Why This Shape Fits

This preserves the current mental model: each command performs one clear stage and emits one stable artifact. The new pipeline wrappers improve ergonomics for common end-to-end runs, but the real contract still lives at the stage layer, which is better for agents, retries, debugging, and testing.

## Input Model

Use a flags-first model with explicit file paths and explicit provider selection.

Why:

- the CLI is agent-primary, but its core operations are concrete file transforms rather than arbitrary JSON payload submission
- explicit paths and flags fit the current v1 ergonomics and existing tests
- users and agents should be able to inspect and re-run individual stages without reconstructing opaque manifests

Provider-bearing generation commands should accept:

- `--provider`
- `--model`
- provider-specific credential overrides when needed

High-level pipeline commands may accept a smaller set of opinionated flags and internally map them onto stage commands.

## Output Model

Primary output surface: stable JSON summaries on stdout.

Secondary output surface: concise human-readable stderr for progress and error context.

The output contract should stay strongly structured. Each command should continue returning a stable top-level summary with command-specific fields plus a small shared core:

- `command`
- `provider` when applicable
- `model` when applicable
- `artifact_type`
- `input_path` or `input_dir` when applicable
- `output_path` or `output_dir`

Additional command-specific fields:

- sheet commands: `rows`, `cols`, `background`
- video commands: `duration_seconds`, `aspect_ratio`, `resolution`
- frame commands: `frame_count`, `fps`
- gif commands: `frames`, `duration_ms`, `loop`, `frame_width`, `frame_height`

Pipeline commands should also return:

- `stages`
- `artifacts`
- `final_output_path`

## Help / Discoverability / Introspection

v2 should improve discoverability because the command tree will become wider.

Expected help behavior:

- top-level help explains the two recommended workflows
- each generation command names supported providers explicitly
- pipeline command help includes “what it does” and “what artifacts it writes”
- compatibility aliases remain documented but clearly marked as legacy entry points

Do not add schema introspection or dynamic provider discovery in v2. A static, well-documented command tree is enough.

## State / Session Model

The CLI remains mostly stateless aside from local files and environment-based credentials. It does not need:

- sessions
- attach/detach
- history
- resumable jobs managed by the CLI itself

Long-running remote generation jobs, especially video generation, should still appear as normal batch commands. Polling happens inside the invocation and the final JSON response summarizes the result.

## Risk / Safety Model

Low-risk operations:

- `template`
- `gif-from-sheet`
- `gif-from-frames`
- `extract-frames`

Medium-risk operations:

- `cutout`
- `cutout-frames`

High-risk operations:

- `generate-sheet`
- `generate-image`
- `generate-video`
- `sheet-pipeline`
- `video-pipeline`

Guardrails:

- keep all output paths explicit
- never delete intermediate artifacts automatically
- fail loudly on incompatible layout metadata
- require explicit rows and cols for sheet-sensitive stages
- require explicit prompt input for generation stages
- preserve compatibility aliases without silently changing semantics

Do not add confirmation prompts in v2. This CLI is automation-facing and the dominant risk is cost or wrong output, not destructive mutation of local state.

## Architecture

### 1. Provider Layer

Introduce a dedicated provider abstraction for remote generation only.

Recommended package shape:

- `ai_gif_skill/providers/base.py`
- `ai_gif_skill/providers/gemini_image.py`
- `ai_gif_skill/providers/gemini_video.py`
- `ai_gif_skill/providers/grok_image.py`
- `ai_gif_skill/providers/grok_video.py`

The provider layer is responsible for:

- credential resolution
- request formatting
- SDK or HTTP invocation
- polling when the remote API is asynchronous
- normalizing results into local file outputs and stable JSON summaries

The provider layer is not responsible for:

- layout metadata policy outside sheet generation
- background removal
- frame extraction
- GIF assembly

### 2. Shared Media Stage Layer

Keep local processing independent from providers.

Recommended stage modules:

- `template.py`
- `cutout.py`
- `gif.py`
- new `frames.py` for extraction and frame-directory operations

Responsibilities:

- `template.py`: keyed sheet template generation
- `cutout.py`: single-image cutout with metadata preservation
- `frames.py`: video-to-frames extraction and directory-wide cutout helpers
- `gif.py`: GIF assembly from sheet or frame directory

### 3. Command Adapters

CLI subcommands should be thin adapters that:

- validate arguments
- call one stage or one pipeline function
- emit JSON

Business logic should stay out of `cli.py`.

## Pipeline Design

### Pipeline A: Sheet Pipeline

Flow:

1. `template`
2. `generate-sheet`
3. `cutout`
4. `gif-from-sheet`

Supported combinations:

- Gemini generates sheet from template
- Grok generates sheet from template

Assumption:

For provider-backed sheet generation, the template PNG remains the strongest way to lock layout and preserve existing v1 quality.

### Pipeline B: Video Pipeline

Flow:

1. `generate-image`
2. `generate-video`
3. `extract-frames`
4. `cutout-frames`
5. `gif-from-frames`

Supported combinations in v2:

- Gemini generates a single image
- Grok generates a single image
- Gemini generates a video from a prompt and optional reference image
- Grok generates a video from a prompt and optional reference image

The pipeline should allow mixed-provider chains. Example:

- Gemini image -> Grok video -> local post-processing
- Grok image -> Gemini video -> local post-processing

The CLI should not force provider coupling between image and video stages.

## Data Contracts

### Sheet Metadata

Keep the current embedded PNG metadata contract for sheet-aware stages. It remains the right guardrail for:

- `generate-sheet`
- `cutout`
- `gif-from-sheet`

### Frame Directory Contract

Introduce a simple manifest for frame directories written by frame-oriented stages, for example:

- `frames_manifest.json`

Suggested fields:

- `frame_count`
- `fps`
- `source_type` (`video` or `generated_frames`)
- `source_path`
- `width`
- `height`
- `background`
- `provider`
- `model`

This keeps frame-based steps inspectable without inventing sessions or a database.

### Provider Result Normalization

All provider-backed generation commands should normalize their result into local files before returning.

For example:

- `generate-sheet` writes one PNG
- `generate-image` writes one PNG
- `generate-video` writes one MP4

The CLI should not expose provider-specific remote URLs as the primary contract, though returning them as optional metadata is acceptable.

## Credential and Dependency Model

Recommended environment variables:

- `GEMINI_API_KEY`
- `XAI_API_KEY`

Dependency strategy:

- keep `Pillow` as core
- keep `rembg` as optional but available for local cutout
- add xAI support without making the rest of the CLI depend on Grok-specific code paths at runtime unless used

If practical, provider-specific SDKs should be isolated so missing dependencies fail only when that provider is invoked.

## Error Handling

v2 should fail loudly and specifically on:

- unknown provider names
- missing required credentials for the selected provider
- layout metadata mismatch
- missing reference image for image-conditioned video when required by the chosen mode
- provider responses that do not contain the expected media artifact
- empty frame directories

Error messages should explain which stage failed and what artifact was expected.

## Testing Strategy

Expand tests in layers:

1. CLI parsing tests
2. provider adapter unit tests with mocked SDK/HTTP responses
3. frame extraction and frame-based GIF tests
4. pipeline orchestration tests with mocked generation stages
5. compatibility tests for legacy aliases

Key regression tests:

- `generate` still maps to sheet generation behavior
- `gif` still maps to sheet slicing behavior
- mixed-provider video pipeline works at the contract level
- frame manifests are written and validated correctly
- sheet metadata still round-trips through sheet commands

## v2 Boundaries

Include in v2:

- provider abstraction for remote generation
- Gemini and Grok image generation support
- Gemini and Grok video generation support
- frame extraction command
- frame-directory cutout command
- GIF assembly from frame directories
- sheet and video pipeline wrapper commands
- compatibility aliases for existing `generate` and `gif`

Defer beyond v2:

- fully automatic provider routing
- cost benchmarking and provider auto-selection
- resumable local job registries
- background worker processes
- one giant `build` command that hides all intermediate stages
- model capability negotiation at runtime

Premature abstraction to avoid:

- one universal provider interface that tries to erase every image vs video difference
- deep manifest systems before simple frame manifests prove insufficient
- converting the CLI into a generic media lab instead of a GIF-oriented workflow tool

## Direction For Implementation

Optimize for:

- preserving v1 strengths
- decoupling providers from local media stages
- making mixed-provider workflows possible
- keeping every artifact inspectable on disk
- stable JSON contracts for agents

Do not optimize for:

- shortest possible command tree
- conversational prompting inside the CLI
- hiding intermediate files
- provider-specific feature completeness in v2 beyond the required image and video paths

Acceptable patterns:

- thin CLI adapters
- provider-specific modules
- shared media-processing helpers
- compatibility aliases with explicit tests
- small pipeline wrappers built on existing stages

Category mistakes:

- putting provider-specific HTTP logic directly in `cli.py`
- making `generate` handle sheet, single-image, and video generation through a tangled flag matrix
- coupling image and video providers so mixed chains become impossible
- collapsing all workflows into one opaque end-to-end command
