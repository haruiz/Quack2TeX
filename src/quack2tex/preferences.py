import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_DUCK_IMAGE = str(Path(__file__).parent / "resources" / "ducks" / "classic-duck.png")

DEFAULT_PREFERENCES = {
    "theme": "neon",
    "duck_image": DEFAULT_DUCK_IMAGE,
    "favorites": [],
    "pomodoro": {
        "work_minutes": 25,
        "rest_minutes": 5,
    },
    "ffmpeg_path": "",
    "presets": {
        "Fast": {"models": "", "capture_mode": "clipboard"},
        "Best": {"models": "", "capture_mode": "screen"},
        "Writing": {"models": "", "capture_mode": "text"},
        "Vision": {"models": "", "capture_mode": "screen"},
        "Local": {"models": "", "capture_mode": "clipboard"},
    },
}


class Preferences:
    """Read and write database-backed application preferences.

    Preferences are stored as JSON values in the local application database.
    Callers should use the typed accessors on this class instead of reading raw
    preference keys directly.
    """

    @classmethod
    def load(cls) -> dict[str, Any]:
        """Load all preferences merged with current defaults.

        Returns:
            Preference dictionary containing defaults for missing keys.
        """
        return cls._merge_with_defaults(cls._load_from_db())

    @classmethod
    def save(cls, data: dict[str, Any]) -> None:
        """Persist preferences after merging them with defaults.

        Args:
            data: Preference values to store.
        """
        cls._save_to_db(cls._merge_with_defaults(data))

    @classmethod
    def _merge_with_defaults(cls, stored: dict[str, Any]) -> dict[str, Any]:
        """Merge stored values with default preference groups.

        Args:
            stored: Raw preference values loaded from the database.

        Returns:
            Complete preference mapping with nested groups populated.
        """
        data = deepcopy(DEFAULT_PREFERENCES)
        data.update(stored or {})
        data["presets"] = {
            **DEFAULT_PREFERENCES["presets"],
            **(stored or {}).get("presets", {}),
        }
        data["pomodoro"] = {
            **DEFAULT_PREFERENCES["pomodoro"],
            **(stored or {}).get("pomodoro", {}),
        }
        return data

    @classmethod
    def _load_from_db(cls) -> dict[str, Any]:
        """Load raw preference values from the database.

        Returns:
            Mapping of preference key to decoded JSON value.
        """
        from quack2tex.repository.db.sync_session import get_db_session
        from quack2tex.repository.models import AppPreference

        with get_db_session() as session:
            preferences = session.query(AppPreference).all()
            return {
                preference.key: preference.decoded_value()
                for preference in preferences
            }

    @classmethod
    def _save_to_db(cls, data: dict[str, Any]) -> None:
        """Replace stored preferences with `data`.

        Args:
            data: Complete preference mapping to encode as JSON values.
        """
        from quack2tex.repository.db.sync_session import get_db_session
        from quack2tex.repository.models import AppPreference

        with get_db_session() as session:
            existing = {
                preference.key: preference
                for preference in session.query(AppPreference).all()
            }
            for key, value in data.items():
                encoded_value = json.dumps(value, sort_keys=True)
                preference = existing.pop(key, None)
                if preference is None:
                    session.add(AppPreference(key=key, value=encoded_value))
                else:
                    preference.value = encoded_value
                    preference.updated_at = datetime.now().astimezone()
            for preference in existing.values():
                session.delete(preference)
            session.commit()

    @classmethod
    def theme(cls) -> str:
        """Return the selected menu theme name."""
        return cls.load().get("theme", DEFAULT_PREFERENCES["theme"])

    @classmethod
    def set_theme(cls, theme: str) -> None:
        """Persist the selected menu theme.

        Args:
            theme: Theme identifier shown in the Preferences panel.
        """
        data = cls.load()
        data["theme"] = theme
        cls.save(data)

    @classmethod
    def duck_image(cls) -> str:
        """Return the configured main duck image path."""
        return str(cls.load().get("duck_image") or "")

    @classmethod
    def set_duck_image(cls, image_path: str) -> None:
        """Persist the main duck image path.

        Args:
            image_path: Local path or Qt resource path for the menu root icon.
        """
        data = cls.load()
        data["duck_image"] = image_path
        cls.save(data)

    @classmethod
    def favorites(cls) -> list[int]:
        """Return favorited menu item ids."""
        return [int(item_id) for item_id in cls.load().get("favorites", [])]

    @classmethod
    def is_favorite(cls, item_id: int) -> bool:
        """Check whether a menu item is favorited.

        Args:
            item_id: Database id of the menu item.

        Returns:
            True when the item is in the favorites list.
        """
        return item_id in cls.favorites()

    @classmethod
    def toggle_favorite(cls, item_id: int) -> bool:
        """Toggle favorite state for a menu item.

        Args:
            item_id: Database id of the menu item.

        Returns:
            True when the item is now favorited, otherwise false.
        """
        data = cls.load()
        favorites = [int(value) for value in data.get("favorites", [])]
        if item_id in favorites:
            favorites.remove(item_id)
            is_favorite = False
        else:
            favorites.append(item_id)
            is_favorite = True
        data["favorites"] = favorites
        cls.save(data)
        return is_favorite

    @classmethod
    def presets(cls) -> dict[str, dict[str, str]]:
        """Return quick-preset definitions keyed by preset name."""
        return cls.load().get("presets", {})

    @classmethod
    def set_preset(cls, name: str, models: str, capture_mode: str) -> None:
        """Persist a quick preset.

        Args:
            name: Preset name shown in the command palette.
            models: Comma-separated model identifiers.
            capture_mode: Input capture mode for the preset.
        """
        data = cls.load()
        data.setdefault("presets", {})[name] = {
            "models": models,
            "capture_mode": capture_mode,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        cls.save(data)

    @classmethod
    def pomodoro(cls) -> dict[str, int]:
        """Return Pomodoro timing settings in minutes."""
        settings = cls.load().get("pomodoro", {})
        return {
            "work_minutes": int(settings.get("work_minutes", DEFAULT_PREFERENCES["pomodoro"]["work_minutes"])),
            "rest_minutes": int(settings.get("rest_minutes", DEFAULT_PREFERENCES["pomodoro"]["rest_minutes"])),
        }

    @classmethod
    def set_pomodoro(cls, work_minutes: int, rest_minutes: int) -> None:
        """Persist Pomodoro timing settings.

        Args:
            work_minutes: Focus duration in minutes. Values below one are clamped.
            rest_minutes: Rest duration in minutes. Values below one are clamped.
        """
        data = cls.load()
        data["pomodoro"] = {
            "work_minutes": max(1, int(work_minutes)),
            "rest_minutes": max(1, int(rest_minutes)),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        cls.save(data)

    @classmethod
    def ffmpeg_path(cls) -> str:
        """Return the configured FFmpeg executable path, or an empty string."""
        return str(cls.load().get("ffmpeg_path") or "").strip()

    @classmethod
    def set_ffmpeg_path(cls, ffmpeg_path: str) -> None:
        """Persist the FFmpeg executable path override.

        Args:
            ffmpeg_path: Absolute path to an FFmpeg binary, or blank for auto-detect.
        """
        data = cls.load()
        data["ffmpeg_path"] = ffmpeg_path.strip()
        cls.save(data)
