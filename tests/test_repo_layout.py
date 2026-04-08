from pathlib import Path


def test_installable_skill_lives_under_skills_directory() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skill_dir = repo_root / "skills" / "ai-gif-skill"

    assert skill_dir.is_dir()
    assert (skill_dir / "SKILL.md").is_file()
    assert (skill_dir / "pyproject.toml").is_file()
    assert (skill_dir / "uv.lock").is_file()
    assert (skill_dir / "agents" / "openai.yaml").is_file()
    assert (skill_dir / "references" / "cli-contract.md").is_file()
    assert (skill_dir / "scripts" / "template_sheet.py").is_file()
    assert (skill_dir / "scripts" / "generate_with_gemini.py").is_file()
    assert (skill_dir / "scripts" / "assemble_gif.py").is_file()
    assert (skill_dir / "scripts" / "generate_image.py").is_file()
    assert (skill_dir / "scripts" / "generate_video.py").is_file()
    assert (skill_dir / "scripts" / "extract_frames.py").is_file()
    assert (skill_dir / "scripts" / "cutout_frames.py").is_file()
    assert (skill_dir / "scripts" / "assemble_gif_from_frames.py").is_file()
    assert (skill_dir / "src" / "ai_gif_skill" / "cli.py").is_file()
