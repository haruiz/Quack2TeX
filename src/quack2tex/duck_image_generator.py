import base64
import colorsys
import json
import re
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from quack2tex.credentials import CredentialStore
from quack2tex.utils import LibUtils


GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image"
GEMINI_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

DUCK_IMAGE_SYSTEM_PROMPT = """Create a Quack2Tex duck avatar that matches the bundled reference ducks.

Style baseline:
- One centered rubber duck character, full body visible, front-facing, looking at the viewer.
- Cute polished 3D/cartoon rendering with soft studio lighting and rounded toy-like forms.
- Square composition with a solid, flat chromakey green background. Use exactly #00FF00 / RGB(0, 255, 0) for the whole background. No scenery, no room, no floor, no shadowed backdrop, no checkerboard pattern, no text, no logos, no watermark.
- Do not add a white outline, border, stroke, sticker edge, glow, drop shadow, or halo around the duck.
- Preserve the recognizable yellow duck beak/body silhouette while adding only the requested costume, props, colors, or theme.
- Do not use green on the duck or props. If green is needed for the concept, use teal or dark forest green instead of chromakey green.
- Keep details readable at small app-icon size and avoid complex backgrounds or extra characters.
"""


@dataclass(frozen=True)
class GeneratedDuck:
    """Metadata for a generated duck image file."""

    path: Path
    label: str


class DuckImageGenerationError(RuntimeError):
    """Raised when Gemini does not return a usable duck image."""


def generated_ducks_dir() -> Path:
    """Return the writable folder for user-generated duck images."""
    output_dir = LibUtils.get_lib_home() / "generated-ducks"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def is_generated_duck_path(path: Path) -> bool:
    """Return whether a path is inside the generated ducks folder."""
    try:
        path.resolve().relative_to(generated_ducks_dir().resolve())
    except ValueError:
        return False
    return True


def generate_duck_image(details: str, reference_paths: list[Path]) -> GeneratedDuck:
    """Generate a new duck image from user details and bundled duck references.

    Args:
        details: User-provided duck concept, such as "Colombian Team Duck Player".
        reference_paths: Existing bundled duck images used as style references.

    Returns:
        Saved generated duck metadata.

    Raises:
        DuckImageGenerationError: If the request cannot be completed.
    """
    concept = details.strip()
    if not concept:
        raise DuckImageGenerationError("Describe the duck you want to generate.")

    api_key = CredentialStore.get_api_key("gemini")
    if not api_key:
        raise DuckImageGenerationError(
            "Configure a Google Gemini API key in Providers before generating ducks."
        )

    payload = {
        "model": GEMINI_IMAGE_MODEL,
        "input": [
            {
                "type": "text",
                "text": _build_duck_prompt(concept),
            },
            *_reference_image_parts(reference_paths[:9]),
        ],
        "response_format": {
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": "1:1",
            "image_size": "1K",
        },
    }
    response = _post_gemini_interaction(api_key, payload)
    image_data = _find_image_data(response)
    if not image_data:
        raise DuckImageGenerationError("Gemini did not return an image.")

    label = concept[:80]
    output_path = _unique_output_path(concept)
    _save_png(image_data, output_path)
    return GeneratedDuck(path=output_path, label=label)


def _build_duck_prompt(concept: str) -> str:
    """Return the complete image prompt sent to Gemini."""
    return (
        f"{DUCK_IMAGE_SYSTEM_PROMPT}\n"
        f"User concept: {concept}\n"
        "Generate one finished square duck avatar for the app. The final image "
        "must show only the front-facing duck on a flat #00FF00 chromakey green background."
    )


def _reference_image_parts(paths: list[Path]) -> list[dict[str, str]]:
    """Build compact base64 image parts for Gemini reference inputs."""
    parts: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.name.endswith("-source.png"):
            continue
        parts.append(
            {
                "type": "image",
                "mime_type": "image/png",
                "data": _reference_png_base64(path),
            }
        )
    return parts


def _reference_png_base64(path: Path) -> str:
    """Return a resized PNG reference as base64."""
    with Image.open(path) as image:
        image = image.convert("RGBA")
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _post_gemini_interaction(api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Call the Gemini Interactions API."""
    request = urllib.request.Request(
        GEMINI_INTERACTIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise DuckImageGenerationError(f"Gemini image generation failed: {message}") from exc
    except urllib.error.URLError as exc:
        raise DuckImageGenerationError(f"Could not reach Gemini: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise DuckImageGenerationError("Gemini returned an invalid response.") from exc


def _find_image_data(value: Any) -> str:
    """Find the first base64 image payload in a Gemini response."""
    if isinstance(value, dict):
        output_image = value.get("output_image") or value.get("outputImage")
        if isinstance(output_image, dict) and isinstance(output_image.get("data"), str):
            return output_image["data"]
        if isinstance(value.get("data"), str) and _looks_like_image_part(value):
            return value["data"]
        for nested in value.values():
            image_data = _find_image_data(nested)
            if image_data:
                return image_data
    if isinstance(value, list):
        for item in value:
            image_data = _find_image_data(item)
            if image_data:
                return image_data
    return ""


def _looks_like_image_part(value: dict[str, Any]) -> bool:
    """Return whether a response object looks like an image block."""
    mime_type = str(value.get("mime_type") or value.get("mimeType") or "")
    block_type = str(value.get("type") or "")
    return mime_type.startswith("image/") or block_type == "image"


def _unique_output_path(concept: str) -> Path:
    """Return a non-conflicting generated-duck output path."""
    slug = re.sub(r"[^a-z0-9]+", "-", concept.lower()).strip("-") or "generated"
    slug = slug[:48].strip("-") or "generated"
    output_dir = generated_ducks_dir()
    candidate = output_dir / f"{slug}-duck.png"
    index = 2
    while candidate.exists():
        candidate = output_dir / f"{slug}-{index}-duck.png"
        index += 1
    return candidate


def _save_png(image_data: str, output_path: Path) -> None:
    """Decode, normalize, and save Gemini image bytes as a square PNG."""
    try:
        raw = base64.b64decode(image_data, validate=True)
    except ValueError as exc:
        raise DuckImageGenerationError("Gemini returned invalid image data.") from exc

    try:
        with Image.open(BytesIO(raw)) as image:
            image = image.convert("RGBA")
            image = remove_green_screen_background(image)
            image = _remove_edge_background(image)
            image = _remove_checkerboard_artifacts(image)
            image = image.resize((1254, 1254), Image.Resampling.LANCZOS)
            image.save(output_path, format="PNG")
    except OSError as exc:
        raise DuckImageGenerationError("Gemini returned an unreadable image.") from exc


def remove_green_screen_background(image: Image.Image) -> Image.Image:
    """Return an RGBA image with chromakey green background made transparent."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    if width == 0 or height == 0:
        return rgba

    mask = [[False for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if _is_chromakey_green(pixels[x, y]):
                mask[y][x] = True

    dilated_mask = _dilate_mask(mask, width, height, radius=1)
    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if dilated_mask[y][x] and _is_green_halo(color):
                pixels[x, y] = (*color[:3], 0)
    _remove_light_edge_halo(rgba)
    return rgba


def _remove_light_edge_halo(image: Image.Image) -> None:
    """Remove thin white or gray halo pixels bordering transparent background."""
    pixels = image.load()
    width, height = image.size
    candidates: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            if not _is_light_desaturated_halo(pixels[x, y]):
                continue
            if _touches_transparency(pixels, width, height, x, y) and _touches_subject_color(
                pixels,
                width,
                height,
                [(x, y)],
            ):
                candidates.append((x, y))

    for x, y in candidates:
        color = pixels[x, y]
        pixels[x, y] = (*color[:3], 0)


def _is_chromakey_green(color: tuple[int, int, int, int]) -> bool:
    """Return whether a color is part of the chromakey green background."""
    red, green, blue, alpha = color
    if alpha < 10:
        return True
    hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    hue_degrees = hue * 360
    return (
        75 <= hue_degrees <= 165
        and saturation >= 0.35
        and value >= 0.25
        and green >= red + 25
        and green >= blue + 25
    )


def _is_green_halo(color: tuple[int, int, int, int]) -> bool:
    """Return whether a color is green spill left at the subject edge."""
    red, green, blue, alpha = color
    if alpha < 10:
        return True
    hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    hue_degrees = hue * 360
    return (
        65 <= hue_degrees <= 175
        and saturation >= 0.18
        and value >= 0.18
        and green >= red + 12
        and green >= blue + 12
    )


def _is_light_desaturated_halo(color: tuple[int, int, int, int]) -> bool:
    """Return whether a color looks like a generated white/gray subject outline."""
    red, green, blue, alpha = color
    if alpha < 250:
        return False
    spread = max(red, green, blue) - min(red, green, blue)
    brightness = (int(red) + int(green) + int(blue)) / 3
    return brightness >= 185 and spread <= 35


def _touches_transparency(
    pixels: Any,
    width: int,
    height: int,
    x: int,
    y: int,
) -> bool:
    """Return whether a pixel is next to transparent background."""
    for next_x in range(max(0, x - 1), min(width, x + 2)):
        for next_y in range(max(0, y - 1), min(height, y + 2)):
            if pixels[next_x, next_y][3] < 10:
                return True
    return False


def _dilate_mask(
    mask: list[list[bool]],
    width: int,
    height: int,
    radius: int,
) -> list[list[bool]]:
    """Dilate a boolean mask by `radius` pixels."""
    dilated = [[False for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if not mask[y][x]:
                continue
            for mask_y in range(max(0, y - radius), min(height, y + radius + 1)):
                for mask_x in range(max(0, x - radius), min(width, x + radius + 1)):
                    dilated[mask_y][mask_x] = True
    return dilated


def _remove_edge_background(image: Image.Image) -> Image.Image:
    """Make connected edge background pixels transparent.

    This preserves normal transparent outputs, and helps when the model returns a
    solid, white, or checkerboard-like background despite the prompt.
    """
    rgba = image.convert("RGBA")
    if _has_meaningful_transparency(rgba):
        return rgba

    pixels = rgba.load()
    width, height = rgba.size
    if width == 0 or height == 0:
        return rgba

    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int, tuple[int, int, int, int]]] = deque()
    for x in range(width):
        queue.append((x, 0, pixels[x, 0]))
        queue.append((x, height - 1, pixels[x, height - 1]))
    for y in range(height):
        queue.append((0, y, pixels[0, y]))
        queue.append((width - 1, y, pixels[width - 1, y]))

    while queue:
        x, y, background_color = queue.popleft()
        if (x, y) in visited or not _similar_color(pixels[x, y], background_color):
            continue
        visited.add((x, y))
        pixels[x, y] = (*pixels[x, y][:3], 0)
        for next_x in range(max(0, x - 1), min(width, x + 2)):
            for next_y in range(max(0, y - 1), min(height, y + 2)):
                if (next_x, next_y) not in visited:
                    queue.append((next_x, next_y, background_color))

    return rgba


def _remove_checkerboard_artifacts(image: Image.Image) -> Image.Image:
    """Remove rendered transparency-checkerboard pixels away from the duck."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    if width == 0 or height == 0:
        return rgba

    protected = _dilated_subject_mask(rgba)
    for y in range(height):
        for x in range(width):
            if protected[y][x]:
                continue
            color = pixels[x, y]
            if color[3] >= 250 and _is_checkerboard_artifact_color(color):
                pixels[x, y] = (*color[:3], 0)
    _remove_small_checkerboard_components(rgba)
    return rgba


def _remove_small_checkerboard_components(image: Image.Image) -> None:
    """Remove tiny neutral components left near the protected duck mask."""
    pixels = image.load()
    width, height = image.size
    visited: set[tuple[int, int]] = set()
    max_component_size = max(6, width * height // 50000)

    for y in range(height):
        for x in range(width):
            if (x, y) in visited or not _is_opaque_checkerboard_pixel(pixels[x, y]):
                continue

            component = _collect_checkerboard_component(
                pixels,
                width,
                height,
                x,
                y,
                visited,
                max_component_size + 1,
            )
            if len(component) <= max_component_size and not _touches_subject_color(
                pixels,
                width,
                height,
                component,
            ):
                for component_x, component_y in component:
                    color = pixels[component_x, component_y]
                    pixels[component_x, component_y] = (*color[:3], 0)


def _collect_checkerboard_component(
    pixels: Any,
    width: int,
    height: int,
    start_x: int,
    start_y: int,
    visited: set[tuple[int, int]],
    limit: int,
) -> list[tuple[int, int]]:
    """Collect a connected neutral checkerboard-like component."""
    component: list[tuple[int, int]] = []
    queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not _is_opaque_checkerboard_pixel(pixels[x, y]):
            continue
        visited.add((x, y))
        component.append((x, y))
        if len(component) > limit:
            continue
        for next_x in range(max(0, x - 1), min(width, x + 2)):
            for next_y in range(max(0, y - 1), min(height, y + 2)):
                if (next_x, next_y) not in visited:
                    queue.append((next_x, next_y))
    return component


def _touches_subject_color(
    pixels: Any,
    width: int,
    height: int,
    component: list[tuple[int, int]],
) -> bool:
    """Return whether a neutral component is attached to colored duck pixels."""
    for x, y in component:
        for next_x in range(max(0, x - 2), min(width, x + 3)):
            for next_y in range(max(0, y - 2), min(height, y + 3)):
                color = pixels[next_x, next_y]
                if color[3] >= 250 and _is_subject_color(color):
                    return True
    return False


def _is_opaque_checkerboard_pixel(color: tuple[int, int, int, int]) -> bool:
    """Return whether an opaque pixel is neutral enough to be checker residue."""
    return color[3] >= 250 and _is_checkerboard_artifact_color(color)


def _dilated_subject_mask(image: Image.Image) -> list[bytearray]:
    """Return a mask around saturated subject pixels to protect low-sat details."""
    pixels = image.load()
    width, height = image.size
    radius = max(6, min(width, height) // 32)
    mask = [bytearray(width) for _ in range(height)]

    for y in range(height):
        for x in range(width):
            color = pixels[x, y]
            if color[3] >= 250 and _is_subject_color(color):
                for mask_y in range(max(0, y - radius), min(height, y + radius + 1)):
                    for mask_x in range(max(0, x - radius), min(width, x + radius + 1)):
                        mask[mask_y][mask_x] = 1
    return mask


def _is_subject_color(color: tuple[int, int, int, int]) -> bool:
    """Return whether a color is likely part of the duck or costume."""
    red, green, blue, _ = color
    return max(red, green, blue) > 70 and max(red, green, blue) - min(red, green, blue) > 38


def _is_checkerboard_artifact_color(color: tuple[int, int, int, int]) -> bool:
    """Return whether a color looks like rendered transparency checkerboard."""
    red, green, blue, _ = color
    spread = max(red, green, blue) - min(red, green, blue)
    brightness = (int(red) + int(green) + int(blue)) / 3
    return spread <= 28 and (brightness >= 170 or brightness <= 70)


def _has_meaningful_transparency(image: Image.Image) -> bool:
    """Return whether an image already contains alpha transparency."""
    alpha = image.getchannel("A")
    return alpha.getextrema()[0] < 250


def _similar_color(
    color: tuple[int, int, int, int],
    background_color: tuple[int, int, int, int],
    tolerance: int = 22,
) -> bool:
    """Return whether two RGBA colors are close enough to be background."""
    if color[3] < 250:
        return True
    return all(
        abs(int(color[index]) - int(background_color[index])) <= tolerance
        for index in range(3)
    )
