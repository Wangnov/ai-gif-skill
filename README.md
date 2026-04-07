# AI GIF Skill Repo

This repository is structured as a `skills.sh`-style skills collection.

Install the skill with:

```bash
npx skills add <owner>/<repo> --skill ai-gif-skill
```

The installable skill lives at:

```text
skills/ai-gif-skill
```

Local verification examples:

```bash
uv run --project skills/ai-gif-skill --extra dev pytest tests
uv run --project skills/ai-gif-skill --with pyyaml python /Users/wangnov/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ai-gif-skill
```
