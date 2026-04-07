from ai_gif_skill.generate import GenerationRequest, build_generation_prompt


def test_build_generation_prompt_preserves_background_and_grid_rules() -> None:
    request = GenerationRequest(
        prompt="a cute blue baby dragon doing a simple walk cycle",
        background="#00FF00",
        rows=2,
        cols=8,
        cell_width=768,
        cell_height=768,
    )

    prompt = build_generation_prompt(request)

    assert "cute blue baby dragon" in prompt
    assert "#00FF00" in prompt
    assert "Do not change the background color" in prompt
    assert "2 rows and 8 columns" in prompt
