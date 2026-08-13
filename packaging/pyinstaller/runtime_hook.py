import os
import sys
from pathlib import Path


def configure_qt_webengine_process() -> None:
    if os.environ.get("QTWEBENGINEPROCESS_PATH"):
        return

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    candidates = [
        bundle_root
        / "PyQt6"
        / "Qt6"
        / "lib"
        / "QtWebEngineCore.framework"
        / "Versions"
        / "A"
        / "Helpers"
        / "QtWebEngineProcess.app"
        / "Contents"
        / "MacOS"
        / "QtWebEngineProcess",
        bundle_root
        / "QtWebEngineCore.framework"
        / "Helpers"
        / "QtWebEngineProcess.app"
        / "Contents"
        / "MacOS"
        / "QtWebEngineProcess",
    ]
    for candidate in candidates:
        if candidate.exists():
            os.environ["QTWEBENGINEPROCESS_PATH"] = str(candidate)
            return


def configure_qt_webengine_resources() -> None:
    if os.environ.get("QTWEBENGINE_RESOURCES_PATH"):
        return

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    candidates = [
        bundle_root
        / "PyQt6"
        / "Qt6"
        / "lib"
        / "QtWebEngineCore.framework"
        / "Versions"
        / "A"
        / "Resources",
        bundle_root
        / "QtWebEngineCore.framework"
        / "Versions"
        / "A"
        / "Resources",
    ]
    for candidate in candidates:
        if (candidate / "qtwebengine_resources.pak").exists():
            os.environ["QTWEBENGINE_RESOURCES_PATH"] = str(candidate)
            locales = candidate / "qtwebengine_locales"
            if locales.exists() and not os.environ.get("QTWEBENGINE_LOCALES_PATH"):
                os.environ["QTWEBENGINE_LOCALES_PATH"] = str(locales)
            return


configure_qt_webengine_process()
configure_qt_webengine_resources()
