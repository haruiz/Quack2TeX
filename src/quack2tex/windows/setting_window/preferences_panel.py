import os
import shutil
from pathlib import Path

from quack2tex.credentials import CredentialStore, CredentialStoreError
from quack2tex.duck_image_generator import (
    DuckImageGenerationError,
    GeneratedDuck,
    generate_duck_image,
    generated_ducks_dir,
    is_generated_duck_path,
)
from quack2tex.preferences import Preferences
from quack2tex.pyqt import (
    QComboBox,
    QFormLayout,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QIcon,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSize,
    QPushButton,
    QMessageBox,
    QThreadPool,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    Signal,
    Qt,
)
from quack2tex.utils import Worker


DUCKS_DIR = Path(__file__).resolve().parents[2] / "resources" / "ducks"
DUCK_LABELS = {
    "classic-duck.png": "Classic",
    "cyber-duck.png": "Cyber",
    "llama-duck.png": "Llama",
    "magic-student-duck.png": "Magic Student",
    "president-duck.png": "President",
    "scientist-duck.png": "Scientist",
    "space-duck.png": "Space",
    "wizard-duck.png": "Wizard",
    "writer-duck.png": "Writer",
}


class PreferencesPanel(QFrame):
    """Tabbed settings panel for non-secret app preferences and quick presets."""

    on_preferences_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the Preferences panel.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.threadpool = QThreadPool()
        self.setObjectName("preferencesPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("preferencesTabs")
        layout.addWidget(self.tabs)

        general_form = self.add_tab("General")
        voice_form = self.add_tab("Voice")
        providers_form = self.add_tab("Providers")
        duck_form = self.add_grid_tab("Duck")
        presets_form = self.add_tab("Presets")

        self.theme_combo = QComboBox(self)
        self.theme_combo.addItems(["neon", "glass", "minimal", "classic"])
        self.theme_combo.setCurrentText(Preferences.theme())
        self.theme_combo.currentTextChanged.connect(self.save_theme)
        general_form.addRow("Menu Theme:", self.theme_combo)

        pomodoro_settings = Preferences.pomodoro()
        self.pomodoro_work_minutes = QSpinBox(self)
        self.pomodoro_work_minutes.setRange(1, 180)
        self.pomodoro_work_minutes.setSuffix(" min")
        self.pomodoro_work_minutes.setValue(pomodoro_settings["work_minutes"])
        self.pomodoro_work_minutes.valueChanged.connect(self.save_pomodoro)
        general_form.addRow("Pomodoro Work:", self.pomodoro_work_minutes)

        self.pomodoro_rest_minutes = QSpinBox(self)
        self.pomodoro_rest_minutes.setRange(1, 60)
        self.pomodoro_rest_minutes.setSuffix(" min")
        self.pomodoro_rest_minutes.setValue(pomodoro_settings["rest_minutes"])
        self.pomodoro_rest_minutes.valueChanged.connect(self.save_pomodoro)
        general_form.addRow("Pomodoro Rest:", self.pomodoro_rest_minutes)

        self.ffmpeg_path_input = QLineEdit(self)
        self.ffmpeg_path_input.setPlaceholderText(self.ffmpeg_placeholder_text())
        self.ffmpeg_path_input.setText(Preferences.ffmpeg_path())
        self.ffmpeg_path_input.setMinimumHeight(38)
        self.ffmpeg_path_input.editingFinished.connect(self.save_ffmpeg_path)

        ffmpeg_row = QWidget(self)
        ffmpeg_row_layout = QHBoxLayout(ffmpeg_row)
        ffmpeg_row_layout.setContentsMargins(0, 0, 0, 0)
        ffmpeg_row_layout.setSpacing(8)
        ffmpeg_row_layout.addWidget(self.ffmpeg_path_input, 1)

        self.ffmpeg_browse_button = QPushButton("Browse", self)
        self.ffmpeg_browse_button.setMinimumHeight(38)
        self.ffmpeg_browse_button.clicked.connect(self.browse_ffmpeg_path)
        ffmpeg_row_layout.addWidget(self.ffmpeg_browse_button)

        self.ffmpeg_clear_button = QPushButton("Auto", self)
        self.ffmpeg_clear_button.setMinimumHeight(38)
        self.ffmpeg_clear_button.clicked.connect(self.clear_ffmpeg_path)
        ffmpeg_row_layout.addWidget(self.ffmpeg_clear_button)

        voice_form.addRow("FFmpeg Path:", ffmpeg_row)

        self.api_key_inputs: dict[str, QLineEdit] = {}
        self.api_key_statuses: dict[str, QLabel] = {}
        self.provider_keys_label = QLabel("Provider API Keys", self)
        self.provider_keys_label.setObjectName("providerKeysLabel")
        providers_form.addRow("", self.provider_keys_label)
        self.add_provider_key_rows(providers_form)

        self.duck_generation_prompt = QTextEdit(self)
        self.duck_generation_prompt.setPlaceholderText(
            'Example: Colombian Team Duck Player'
        )
        self.duck_generation_prompt.setMinimumHeight(72)
        self.duck_generation_prompt.setMaximumHeight(96)
        duck_form.addWidget(self.form_label("New Duck Details:"), 0, 0, Qt.AlignmentFlag.AlignTop)
        duck_form.addWidget(self.duck_generation_prompt, 0, 1)

        duck_generation_row = QWidget(self)
        duck_generation_layout = QHBoxLayout(duck_generation_row)
        duck_generation_layout.setContentsMargins(0, 0, 0, 0)
        duck_generation_layout.setSpacing(8)

        self.generate_duck_button = QPushButton("Generate Duck", self)
        self.generate_duck_button.setMinimumHeight(38)
        self.generate_duck_button.clicked.connect(self.start_duck_generation)
        duck_generation_layout.addWidget(self.generate_duck_button)

        self.duck_generation_status = QLabel(self)
        self.duck_generation_status.setWordWrap(True)
        duck_generation_layout.addWidget(self.duck_generation_status, 1)
        duck_form.addWidget(duck_generation_row, 1, 1)

        self.duck_picker = QListWidget(self)
        self.duck_picker.setObjectName("duckPicker")
        self.duck_picker.setViewMode(QListWidget.ViewMode.IconMode)
        self.duck_picker.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.duck_picker.setMovement(QListWidget.Movement.Static)
        self.duck_picker.setSpacing(12)
        self.duck_picker.setWrapping(True)
        self.duck_picker.setUniformItemSizes(True)
        self.duck_picker.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.duck_picker.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.duck_picker.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.duck_picker.setIconSize(QSize(72, 72))
        self.duck_picker.setGridSize(QSize(142, 116))
        self.duck_picker.setMinimumHeight(420)
        self.duck_picker.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.duck_picker.currentItemChanged.connect(self.save_duck_image)
        self.duck_picker.currentItemChanged.connect(self.update_delete_duck_button)
        self.populate_duck_picker()
        duck_form.addWidget(self.form_label("Duck Image:"), 2, 0, Qt.AlignmentFlag.AlignTop)
        duck_form.addWidget(self.duck_picker, 2, 1)

        self.delete_duck_button = QPushButton("Delete Generated Duck", self)
        self.delete_duck_button.setMinimumHeight(38)
        self.delete_duck_button.clicked.connect(self.delete_generated_duck)
        duck_form.addWidget(self.delete_duck_button, 3, 1)
        self.update_delete_duck_button()

        self.presets_label = QLabel(self)
        self.presets_label.setWordWrap(True)
        self.refresh_preset_text()
        presets_form.addRow("Quick Presets:", self.presets_label)

        self.preset_name = QComboBox(self)
        self.preset_name.addItems(list(Preferences.presets().keys()))
        presets_form.addRow("Preset Name:", self.preset_name)

        self.preset_models = QLineEdit(self)
        self.preset_models.setPlaceholderText("comma,separated,model,names")
        presets_form.addRow("Preset Models:", self.preset_models)

        self.preset_capture_mode = QComboBox(self)
        self.preset_capture_mode.addItems(["clipboard", "screen", "text", "voice"])
        presets_form.addRow("Preset Capture:", self.preset_capture_mode)

        self.preset_name.currentTextChanged.connect(self.load_preset)
        self.load_preset(self.preset_name.currentText())

        self.preset_actions = QWidget(self)
        self.preset_actions.setObjectName("presetActions")
        preset_actions_layout = QHBoxLayout(self.preset_actions)
        preset_actions_layout.setContentsMargins(18, 12, 18, 12)
        preset_actions_layout.setSpacing(8)
        preset_actions_layout.addStretch(1)

        self.reset_presets_button = QPushButton("Reset Presets", self)
        self.reset_presets_button.clicked.connect(self.reset_presets)
        preset_actions_layout.addWidget(self.reset_presets_button)

        self.save_preset_button = QPushButton("Save Preset", self)
        self.save_preset_button.clicked.connect(self.save_preset)
        preset_actions_layout.addWidget(self.save_preset_button)
        layout.addWidget(self.preset_actions)
        self.tabs.currentChanged.connect(self.update_preset_actions_visibility)
        self.update_preset_actions_visibility()

    def add_tab(self, title: str, fill_content: bool = False) -> QFormLayout:
        """Create a scrollable Preferences sub-tab.

        Args:
            title: Tab label.
            fill_content: Whether the form should consume remaining tab height.

        Returns:
            Form layout where settings rows should be added.
        """
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("preferencesScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget(scroll_area)
        content.setObjectName("preferencesContent")
        scroll_area.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        content_layout.addLayout(form, 1 if fill_content else 0)
        if not fill_content:
            content_layout.addStretch()

        self.tabs.addTab(scroll_area, title)
        return form

    def add_grid_tab(self, title: str) -> QGridLayout:
        """Create a scrollable Preferences sub-tab whose rows can stretch."""
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("preferencesScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget(scroll_area)
        content.setObjectName("preferencesContent")
        scroll_area.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(2, 1)
        content_layout.addLayout(grid, 1)

        self.tabs.addTab(scroll_area, title)
        return grid

    def form_label(self, text: str) -> QLabel:
        """Create a label matching QFormLayout row labels."""
        label = QLabel(text, self)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        return label

    def add_provider_key_rows(self, form: QFormLayout) -> None:
        """Add API-key controls for each credential provider.

        Args:
            form: Target form layout on the Providers tab.
        """
        for provider in CredentialStore.providers():
            row = QWidget(self)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            api_key_input = QLineEdit(self)
            api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            api_key_input.setPlaceholderText("Leave blank to keep the current key")
            api_key_input.setMinimumHeight(38)
            row_layout.addWidget(api_key_input, 1)

            save_button = QPushButton("Save", self)
            save_button.setMinimumHeight(38)
            save_button.clicked.connect(
                lambda checked=False, name=provider.name: self.save_api_key(name)
            )
            row_layout.addWidget(save_button)

            clear_button = QPushButton("Clear", self)
            clear_button.setMinimumHeight(38)
            clear_button.clicked.connect(
                lambda checked=False, name=provider.name: self.clear_api_key(name)
            )
            row_layout.addWidget(clear_button)

            status = QLabel(self)
            status.setMinimumWidth(180)
            row_layout.addWidget(status)

            self.api_key_inputs[provider.name] = api_key_input
            self.api_key_statuses[provider.name] = status
            form.addRow(f"{provider.label}:", row)
            self.refresh_api_key_status(provider.name)

    def refresh_api_key_status(self, provider_name: str) -> None:
        """Refresh the visible credential status for one provider.

        Args:
            provider_name: Internal provider identifier.
        """
        provider = CredentialStore.provider(provider_name)
        status = self.api_key_statuses[provider_name]
        env_value = os.getenv(provider.env_var)
        try:
            stored_value = CredentialStore.get_api_key(provider_name, include_env=False)
        except CredentialStoreError:
            if env_value:
                status.setText(f"Using {provider.env_var}")
                return
            status.setText("Secure storage unavailable")
            return
        if stored_value:
            status.setText("Saved securely")
        elif env_value:
            status.setText(f"Using {provider.env_var}")
        else:
            status.setText("Not configured")

    def save_api_key(self, provider_name: str) -> None:
        """Save one provider API key to secure storage.

        Args:
            provider_name: Internal provider identifier.
        """
        api_key_input = self.api_key_inputs[provider_name]
        api_key = api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Missing API Key", "Enter an API key before saving.")
            return
        try:
            CredentialStore.set_api_key(provider_name, api_key)
        except (CredentialStoreError, ValueError) as exc:
            QMessageBox.warning(self, "Unable to Save API Key", str(exc))
            return
        api_key_input.clear()
        self.refresh_api_key_status(provider_name)
        self.on_preferences_changed.emit()

    def clear_api_key(self, provider_name: str) -> None:
        """Remove one provider API key from secure storage.

        Args:
            provider_name: Internal provider identifier.
        """
        try:
            CredentialStore.delete_api_key(provider_name)
        except CredentialStoreError as exc:
            QMessageBox.warning(self, "Unable to Clear API Key", str(exc))
            return
        self.api_key_inputs[provider_name].clear()
        self.refresh_api_key_status(provider_name)
        self.on_preferences_changed.emit()

    def duck_options(self) -> list[Path]:
        """Return available bundled and user-generated duck image paths."""
        duck_paths: list[Path] = []
        if DUCKS_DIR.exists():
            duck_paths.extend(
                sorted(
                    path
                    for path in DUCKS_DIR.glob("*-duck.png")
                    if not path.name.endswith("-source.png")
                )
            )
        custom_dir = generated_ducks_dir()
        duck_paths.extend(sorted(custom_dir.glob("*-duck.png")))
        return duck_paths

    def duck_label(self, path: Path) -> str:
        """Return a display label for a duck image path.

        Args:
            path: Duck image path.

        Returns:
            Human-readable label.
        """
        return DUCK_LABELS.get(path.name, path.stem.replace("-", " ").title())

    def populate_duck_picker(self) -> None:
        """Populate the duck image picker and select the current preference."""
        current = Preferences.duck_image()
        self.duck_picker.blockSignals(True)
        self.duck_picker.clear()
        for path in self.duck_options():
            item = QListWidgetItem(QIcon(str(path)), self.duck_label(path))
            item.setToolTip(f"Use {self.duck_label(path)} as the main menu duck")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.duck_picker.addItem(item)
            if current and Path(current) == path:
                self.duck_picker.setCurrentItem(item)

        if not current and self.duck_picker.count():
            self.duck_picker.setCurrentRow(0)
        self.duck_picker.blockSignals(False)
        self.update_delete_duck_button()

    def start_duck_generation(self) -> None:
        """Start generating a new duck image from the Duck preferences tab."""
        details = self.duck_generation_prompt.toPlainText().strip()
        if not details:
            QMessageBox.warning(
                self,
                "Missing Duck Details",
                "Describe the duck you want to generate.",
            )
            return

        self.generate_duck_button.setEnabled(False)
        self.duck_generation_status.setText("Generating duck image...")
        worker = Worker(self.do_generate_duck, details)
        worker.signals.result.connect(self.done_generate_duck)
        worker.signals.error.connect(self.error_generate_duck)
        worker.signals.finished.connect(
            lambda: self.generate_duck_button.setEnabled(True)
        )
        self.threadpool.start(worker)

    def do_generate_duck(self, details: str) -> GeneratedDuck:
        """Generate a duck image in a background worker."""
        return generate_duck_image(details, self.bundled_duck_references())

    def bundled_duck_references(self) -> list[Path]:
        """Return bundled duck images used as Gemini style references."""
        if not DUCKS_DIR.exists():
            return []
        return sorted(
            path
            for path in DUCKS_DIR.glob("*-duck.png")
            if not path.name.endswith("-source.png")
        )

    def done_generate_duck(self, generated_duck: GeneratedDuck) -> None:
        """Add a generated duck to the picker and select it."""
        Preferences.set_duck_image(str(generated_duck.path))
        self.populate_duck_picker()
        self.select_duck_image(generated_duck.path)
        self.duck_generation_status.setText(f"Generated {generated_duck.label}.")
        self.duck_generation_prompt.clear()
        self.on_preferences_changed.emit()

    def error_generate_duck(self, error: tuple[type[BaseException], BaseException, str]) -> None:
        """Show a duck-generation error."""
        _, value, _ = error
        if isinstance(value, DuckImageGenerationError):
            message = str(value)
        else:
            message = "Duck image generation failed. Check the Gemini API key and try again."
        self.duck_generation_status.setText(message)
        QMessageBox.warning(self, "Unable to Generate Duck", message)

    def select_duck_image(self, image_path: Path) -> None:
        """Select a duck image in the picker by path."""
        target = str(image_path)
        for index in range(self.duck_picker.count()):
            item = self.duck_picker.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == target:
                self.duck_picker.setCurrentItem(item)
                return

    def update_delete_duck_button(self) -> None:
        """Enable generated-duck deletion only for user-generated files."""
        if not hasattr(self, "delete_duck_button"):
            return
        image_path = self.selected_duck_path()
        self.delete_duck_button.setEnabled(
            bool(image_path and is_generated_duck_path(image_path))
        )

    def selected_duck_path(self) -> Path | None:
        """Return the currently selected duck image path."""
        item = self.duck_picker.currentItem()
        if item is None:
            return None
        image_path = item.data(Qt.ItemDataRole.UserRole)
        if not image_path:
            return None
        return Path(str(image_path))

    def delete_generated_duck(self) -> None:
        """Delete the selected generated duck image from local storage."""
        image_path = self.selected_duck_path()
        if image_path is None or not is_generated_duck_path(image_path):
            QMessageBox.information(
                self,
                "Bundled Duck",
                "Only generated duck images can be deleted.",
            )
            return

        label = self.duck_label(image_path)
        answer = QMessageBox.question(
            self,
            "Delete Generated Duck",
            f"Delete {label} from generated ducks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            image_path.unlink(missing_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, "Unable to Delete Duck", str(exc))
            return

        fallback = self.default_duck_option()
        if fallback is not None:
            Preferences.set_duck_image(str(fallback))
        else:
            Preferences.set_duck_image("")
        self.populate_duck_picker()
        if fallback is not None:
            self.select_duck_image(fallback)
        self.duck_generation_status.setText(f"Deleted {label}.")
        self.on_preferences_changed.emit()

    def default_duck_option(self) -> Path | None:
        """Return the bundled duck used after deleting a generated duck."""
        references = self.bundled_duck_references()
        if references:
            return references[0]
        options = self.duck_options()
        return options[0] if options else None

    def save_theme(self, theme: str) -> None:
        """Persist the selected theme.

        Args:
            theme: Theme name selected in the UI.
        """
        Preferences.set_theme(theme)
        self.on_preferences_changed.emit()

    def save_pomodoro(self) -> None:
        """Persist Pomodoro work/rest values from the spin boxes."""
        Preferences.set_pomodoro(
            self.pomodoro_work_minutes.value(),
            self.pomodoro_rest_minutes.value(),
        )
        self.on_preferences_changed.emit()

    def save_ffmpeg_path(self) -> None:
        """Persist the FFmpeg path from the Voice tab."""
        Preferences.set_ffmpeg_path(self.ffmpeg_path_input.text())
        self.on_preferences_changed.emit()

    def browse_ffmpeg_path(self) -> None:
        """Open a file picker and save the selected FFmpeg executable."""
        current_path = self.ffmpeg_path_input.text().strip()
        start_dir = str(Path(current_path).parent) if current_path else "/opt/homebrew/bin"
        ffmpeg_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FFmpeg",
            start_dir,
            "Executable files (*)",
        )
        if not ffmpeg_path:
            return
        self.ffmpeg_path_input.setText(ffmpeg_path)
        self.save_ffmpeg_path()

    def clear_ffmpeg_path(self) -> None:
        """Clear the FFmpeg override so auto-detection is used."""
        self.ffmpeg_path_input.clear()
        self.save_ffmpeg_path()

    def ffmpeg_placeholder_text(self) -> str:
        """Return placeholder text showing the auto-detected FFmpeg path."""
        ffmpeg_path = self.auto_detect_ffmpeg_path()
        if ffmpeg_path:
            return f"Auto-detect ({ffmpeg_path})"
        return "Auto-detect from PATH or Homebrew"

    def auto_detect_ffmpeg_path(self) -> str:
        """Return the first common FFmpeg path that exists locally."""
        for candidate in (
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
            shutil.which("ffmpeg") or "",
        ):
            if candidate and Path(candidate).exists():
                return candidate
        return ""

    def save_duck_image(self, item: QListWidgetItem | None = None) -> None:
        """Persist the selected duck image.

        Args:
            item: Selected list item from the duck picker.
        """
        if item is None:
            return
        image_path = item.data(Qt.ItemDataRole.UserRole)
        if image_path:
            Preferences.set_duck_image(str(image_path))
            self.on_preferences_changed.emit()

    def refresh_preset_text(self) -> None:
        """Refresh the summary list of quick presets."""
        presets = Preferences.presets()
        lines = [
            f"{name}: {value.get('capture_mode') or 'default'}"
            for name, value in presets.items()
        ]
        self.presets_label.setText("\n".join(lines))

    def update_preset_actions_visibility(self) -> None:
        """Show preset action buttons only when the Presets tab is active."""
        self.preset_actions.setVisible(self.tabs.tabText(self.tabs.currentIndex()) == "Presets")

    def load_preset(self, name: str) -> None:
        """Load a quick preset into the edit controls.

        Args:
            name: Preset name selected in the combo box.
        """
        preset = Preferences.presets().get(name, {})
        self.preset_models.setText(preset.get("models", ""))
        self.preset_capture_mode.setCurrentText(preset.get("capture_mode", "clipboard"))

    def save_preset(self) -> None:
        """Persist the quick preset currently shown in the edit controls."""
        Preferences.set_preset(
            self.preset_name.currentText(),
            self.preset_models.text().strip(),
            self.preset_capture_mode.currentText(),
        )
        self.refresh_preset_text()
        self.on_preferences_changed.emit()

    def reset_presets(self) -> None:
        """Reset quick presets to defaults."""
        data = Preferences.load()
        data.pop("presets", None)
        Preferences.save(data)
        self.refresh_preset_text()
        self.preset_name.clear()
        self.preset_name.addItems(list(Preferences.presets().keys()))
        self.on_preferences_changed.emit()
