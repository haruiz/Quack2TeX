from enum import Enum


class CaptureMode(str, Enum):
    SCREEN = "screen"
    CLIPBOARD = "clipboard"
    VOICE = "voice"
    TEXT = "text"

