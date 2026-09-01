import base64
from io import BytesIO

from PIL import Image

from quack2tex import duck_image_generator


def test_build_duck_prompt_includes_style_baseline_and_user_concept() -> None:
    prompt = duck_image_generator._build_duck_prompt("Colombian Team Duck Player")

    assert "Quack2Tex duck avatar" in prompt
    assert "Colombian Team Duck Player" in prompt
    assert "no text" in prompt
    assert "front-facing" in prompt
    assert "#00FF00 chromakey green background" in prompt
    assert "no checkerboard pattern" in prompt
    assert "Do not add a white outline" in prompt


def test_find_image_data_supports_output_image_and_nested_parts() -> None:
    assert duck_image_generator._find_image_data(
        {"output_image": {"data": "abc"}}
    ) == "abc"
    assert duck_image_generator._find_image_data(
        {"outputImage": {"data": "camel"}}
    ) == "camel"
    assert duck_image_generator._find_image_data(
        {"steps": [{"parts": [{"type": "image", "data": "nested"}]}]}
    ) == "nested"


def test_reference_image_parts_skips_source_images(tmp_path) -> None:
    image_path = tmp_path / "sample-duck.png"
    source_path = tmp_path / "sample-duck-source.png"
    Image.new("RGBA", (12, 12), (255, 200, 0, 255)).save(image_path)
    Image.new("RGBA", (12, 12), (255, 200, 0, 255)).save(source_path)

    parts = duck_image_generator._reference_image_parts([image_path, source_path])

    assert len(parts) == 1
    assert parts[0]["type"] == "image"
    assert parts[0]["mime_type"] == "image/png"
    assert base64.b64decode(parts[0]["data"])


def test_save_png_normalizes_generated_image_size(tmp_path) -> None:
    buffer = BytesIO()
    Image.new("RGB", (16, 16), (255, 200, 0)).save(buffer, format="PNG")
    image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    output_path = tmp_path / "generated-duck.png"

    duck_image_generator._save_png(image_data, output_path)

    with Image.open(output_path) as image:
        assert image.size == (1254, 1254)
        assert image.mode == "RGBA"


def test_remove_green_screen_background_uses_chromakey_mask() -> None:
    image = Image.new("RGBA", (12, 12), (0, 255, 0, 255))
    pixels = image.load()
    for x in range(4, 8):
        for y in range(4, 8):
            pixels[x, y] = (255, 200, 0, 255)
    for x in range(3, 9):
        pixels[x, 3] = (245, 255, 245, 255)
        pixels[x, 8] = (245, 255, 245, 255)
    pixels[3, 4] = (65, 230, 40, 255)

    cleaned = duck_image_generator.remove_green_screen_background(image)
    cleaned_pixels = cleaned.load()

    assert cleaned_pixels[0, 0][3] == 0
    assert cleaned_pixels[3, 4][3] == 0
    assert cleaned_pixels[4, 4][3] == 255
    assert cleaned_pixels[3, 3][3] == 0


def test_remove_green_screen_background_removes_light_edge_halo() -> None:
    image = Image.new("RGBA", (12, 12), (0, 255, 0, 255))
    pixels = image.load()
    for x in range(4, 8):
        for y in range(4, 8):
            pixels[x, y] = (255, 200, 0, 255)
    for y in range(4, 8):
        pixels[3, y] = (230, 232, 230, 255)
    pixels[6, 6] = (245, 245, 245, 255)

    cleaned = duck_image_generator.remove_green_screen_background(image)
    cleaned_pixels = cleaned.load()

    assert cleaned_pixels[3, 5][3] == 0
    assert cleaned_pixels[6, 6][3] == 255


def test_save_png_removes_checkerboard_edge_background(tmp_path) -> None:
    image = Image.new("RGBA", (40, 40), (15, 23, 37, 255))
    pixels = image.load()
    for x in range(8, 32):
        for y in range(8, 32):
            if (x + y) % 2 == 0:
                pixels[x, y] = (245, 245, 245, 255)
            else:
                pixels[x, y] = (55, 55, 55, 255)
    for x in range(16, 24):
        for y in range(16, 24):
            pixels[x, y] = (255, 200, 0, 255)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    output_path = tmp_path / "generated-duck.png"

    duck_image_generator._save_png(image_data, output_path)

    with Image.open(output_path) as saved_image:
        saved_image = saved_image.convert("RGBA")
        assert saved_image.getpixel((0, 0))[3] == 0
        assert saved_image.getpixel((627, 627))[3] > 200
        assert saved_image.getpixel((300, 300))[3] <= 5


def test_checkerboard_cleanup_removes_isolated_dots_near_duck() -> None:
    image = Image.new("RGBA", (36, 36), (0, 0, 0, 0))
    pixels = image.load()
    for x in range(12, 24):
        for y in range(12, 24):
            pixels[x, y] = (255, 200, 0, 255)

    pixels[8, 14] = (245, 245, 245, 255)
    pixels[27, 19] = (55, 55, 55, 255)
    for x in range(10, 14):
        for y in range(25, 29):
            pixels[x, y] = (245, 245, 245, 255)
    pixels[14, 26] = (255, 200, 0, 255)

    cleaned = duck_image_generator._remove_checkerboard_artifacts(image)
    cleaned_pixels = cleaned.load()

    assert cleaned_pixels[8, 14][3] == 0
    assert cleaned_pixels[27, 19][3] == 0
    assert cleaned_pixels[11, 26][3] == 255


def test_is_generated_duck_path_checks_generated_folder(monkeypatch, tmp_path) -> None:
    generated_dir = tmp_path / "generated-ducks"
    generated_dir.mkdir()
    generated_duck = generated_dir / "custom-duck.png"
    bundled_duck = tmp_path / "classic-duck.png"

    monkeypatch.setattr(
        duck_image_generator,
        "generated_ducks_dir",
        lambda: generated_dir,
    )

    assert duck_image_generator.is_generated_duck_path(generated_duck)
    assert not duck_image_generator.is_generated_duck_path(bundled_duck)


def test_generate_duck_image_requests_jpeg_response(monkeypatch, tmp_path) -> None:
    reference_path = tmp_path / "classic-duck.png"
    Image.new("RGBA", (12, 12), (255, 200, 0, 255)).save(reference_path)

    buffer = BytesIO()
    Image.new("RGB", (16, 16), (255, 200, 0)).save(buffer, format="JPEG")
    image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

    captured_payload = {}

    monkeypatch.setattr(
        duck_image_generator.CredentialStore,
        "get_api_key",
        lambda provider_name: "test-key",
    )
    monkeypatch.setattr(
        duck_image_generator,
        "generated_ducks_dir",
        lambda: tmp_path,
    )

    def fake_post(api_key, payload):
        captured_payload.update(payload)
        return {"output_image": {"data": image_data}}

    monkeypatch.setattr(duck_image_generator, "_post_gemini_interaction", fake_post)

    result = duck_image_generator.generate_duck_image(
        "Colombian Team Duck Player",
        [reference_path],
    )

    assert result.path.exists()
    assert captured_payload["response_format"]["mime_type"] == "image/jpeg"
