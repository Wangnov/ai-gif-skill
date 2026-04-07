# AI GIF Skill Design

**Goal:** Build an agent-first skill that turns a keyed sprite-sheet template into a generated sprite sheet, removes the background, and assembles a final GIF, and package it in a `skills.sh`-style repository layout.

## Purpose

Provide a stable four-stage pipeline for sprite-sheet asset generation.

Repository layout:

- repo root is a skills collection
- installable skill lives under `skills/ai-gif-skill`
- development-only tests and docs stay at repo root

Pipeline stages:

1. template
2. generate
3. cutout
4. gif

## Classification

- Primary role: Workflow / Orchestration
- Primary user type: Agent-Primary
- Primary interaction form: Batch CLI
- Statefulness: Config-Stateful
- Risk profile: Mixed
- Secondary surfaces: Human-readable stderr, skill-guided user questioning

## Design Stance

Optimize for explicit paths, stable JSON, and easy stage-by-stage retry. Avoid hidden sessions, daemons, or heavy orchestration state in v1. Keep the installable skill self-contained inside `skills/ai-gif-skill`.

## Command Shape

- `template`: create SVG/PNG keyed sheet
- `generate`: call Gemini with the template image and built-in prompt rules
- `cutout`: remove the keyed background with rembg
- `gif`: slice frames and assemble the animation

## v1 Boundaries

- Include stage-by-stage commands only
- Defer one-shot `build`
- Defer durable job manifests
- Defer multi-model routing and model benchmarking
