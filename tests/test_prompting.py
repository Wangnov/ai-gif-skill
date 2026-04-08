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
    assert "EXACTLY 16 frames" in prompt
    assert "Do not output a different panel count or grid layout than the template" in prompt


def test_build_generation_prompt_adapts_frame_count_to_requested_layout() -> None:
    request = GenerationRequest(
        prompt="an original cute fox creature doing a simple idle loop",
        background="#00FF00",
        rows=3,
        cols=3,
        cell_width=512,
        cell_height=512,
    )

    prompt = build_generation_prompt(request)

    assert "3 rows and 3 columns" in prompt
    assert "EXACTLY 9 frames" in prompt


def test_build_generation_prompt_locks_anchor_and_rejects_whole_character_drift() -> None:
    request = GenerationRequest(
        prompt="an original cute fox creature doing a clean idle loop",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=384,
        cell_height=384,
    )

    prompt = build_generation_prompt(request)

    assert "same camera angle, framing, and scale" in prompt
    assert "Keep the character centered in each cell" in prompt
    assert "Do not animate by sliding the whole character sideways" in prompt
    assert "No horizontal drift. No vertical drift." in prompt
    assert "The animation must come from pose changes between frames" in prompt


def test_build_generation_prompt_requires_more_than_facial_motion() -> None:
    request = GenerationRequest(
        prompt="an original cute fox creature doing a clean idle loop",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=384,
        cell_height=384,
    )

    prompt = build_generation_prompt(request)

    assert "Do not limit the animation to blinking, eye changes, or tiny facial changes alone" in prompt
    assert "Make sure multiple frames show visible silhouette or body-part changes" in prompt


def test_build_generation_prompt_locks_view_direction_by_default() -> None:
    request = GenerationRequest(
        prompt="an original cute fox creature doing a clean idle loop",
        background="#00FF00",
        rows=2,
        cols=4,
        cell_width=384,
        cell_height=384,
    )

    prompt = build_generation_prompt(request)

    assert "Keep the same facing direction and view orientation across frames" in prompt
    assert "Do not turn the character into a different camera view or profile unless the asset request explicitly asks for that" in prompt
