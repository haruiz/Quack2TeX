import typing
import re
import threading

from pathlib import Path

from modihub.llm import LLM
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from quack2tex.pyqt import (
    QTabWidget, QDialog, QVBoxLayout, QWidget, QPushButton,
    QApplication, QIcon, QCursor, Qt, QHBoxLayout, QThreadPool, Slot, Signal,
    QTextEdit, QDialogButtonBox
)
from quack2tex.credentials import CredentialStore
from quack2tex.repository import PromptRepository
from quack2tex.resources import *  # noqa: F401
from quack2tex.utils import Worker, run_async
from quack2tex.widgets import MarkdownViewer
from quack2tex.repository.db.sync_session import get_db_session

class OutputDialog(QDialog):
    """Display model outputs and actions for copy, export, edit, retry, and save.

    Args:
        prompt_info: Prompt metadata, input, and model outputs produced by the
            main prompt workflow.
        parent: Optional parent widget.

    Attributes:
        retry_requested: Emitted with a model name when the user retries output
            generation for one model.
    """
    retry_requested = Signal(str)

    def __init__(self, prompt_info: dict, parent: QWidget | None = None) -> None:
        """Initialize the output dialog.

        Args:
            prompt_info: Prompt data, prompt input, and model response mapping.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("outputDialog")
        self.setWindowTitle("Model Output Viewer")
        self.setMinimumSize(900, 640)

        self.threadpool = QThreadPool()
        self.prompt_info: dict = prompt_info
        self.prompt_id: int | None = None
        self.save_buttons: dict[str, QPushButton] = {}
        self.saving_models: set[str] = set()
        self.saved_models: set[str] = set()
        self.save_lock = threading.Lock()

        self.tabs = QTabWidget()
        self.tabs.setObjectName("outputTabs")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        self.layout.addWidget(self.tabs)

        self.populate_toolbox()


    def populate_toolbox(self) -> None:
        """Create one output tab per model response."""
        prompt_result = self.prompt_info.get("prompt_result", {})
        for model_name, model_output in prompt_result.items():
            self.tabs.addTab(
                self.create_toolbox_page(model_name, model_output),
                model_name
            )

    def create_toolbox_page(self, model_name: str, model_output: str) -> QWidget:
        """Create a tab page for a single model output.

        Args:
            model_name: Model identifier for the tab label and actions.
            model_output: Markdown/text output to show.

        Returns:
            Widget containing the toolbar and markdown viewer.
        """
        widget = QWidget()
        widget.setObjectName("outputPage")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        viewer = MarkdownViewer()
        viewer.setObjectName("outputMarkdownViewer")
        viewer.content = model_output

        toolbar = QWidget()
        toolbar.setObjectName("outputToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        toolbar_layout.setSpacing(8)

        btn_copy = self._make_icon_button(":icons/copy-clipboard.png", "Copy to clipboard")
        btn_copy.clicked.connect(lambda _, content=model_output: self.on_copy_text(content))

        btn_save = self._make_icon_button(":icons/save.png", "Save to database")
        btn_save.clicked.connect(lambda _, model=model_name: self.on_save_to_db(model))
        self.save_buttons[model_name] = btn_save

        btn_export = self._make_icon_button(":icons/broom.png", "Save output to Markdown file")
        btn_export.clicked.connect(lambda _, model=model_name, content=model_output: self.on_export(model, content))

        btn_editor = self._make_icon_button(":icons/edit.png", "Open output in editor")
        btn_editor.clicked.connect(lambda _, model=model_name, content=model_output: self.on_open_editor(model, content))

        btn_retry = self._make_icon_button(":icons/refresh.png", "Retry this prompt with this model")
        btn_retry.clicked.connect(lambda _, model=model_name: self.retry_requested.emit(model))

        toolbar_layout.addWidget(btn_copy)
        toolbar_layout.addWidget(btn_save)
        toolbar_layout.addWidget(btn_export)
        toolbar_layout.addWidget(btn_editor)
        toolbar_layout.addWidget(btn_retry)
        toolbar_layout.addStretch(1)

        layout.addWidget(toolbar)
        layout.addWidget(viewer)
        return widget

    def _make_icon_button(self, icon_path: str, tooltip: str) -> QPushButton:
        """Create a fixed-size toolbar button.

        Args:
            icon_path: Qt resource path for the button icon.
            tooltip: Tooltip text shown on hover.

        Returns:
            Configured icon button.
        """
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setObjectName("outputActionButton")
        btn.setToolTip(tooltip)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedSize(42, 42)
        return btn

    @Slot(str)
    def on_copy_text(self, content: str) -> None:
        """Copy output content to the system clipboard.

        Args:
            content: Text to copy.
        """
        QApplication.clipboard().setText(content)

    @Slot(str, str)
    def on_export(self, model_name: str, content: str) -> None:
        """Export model output to a user-selected file.

        Args:
            model_name: Model identifier used for the default filename.
            content: Output content to write.
        """
        safe_name = model_name.replace("/", "-").replace(":", "-")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output",
            str(Path.home() / f"quack2tex-{safe_name}.md"),
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            Path(file_path).write_text(content, encoding="utf-8")

    @Slot(str, str)
    def on_open_editor(self, model_name: str, content: str) -> None:
        """Open an editable output preview with a Copy action.

        Args:
            model_name: Model identifier shown in the editor title.
            content: Initial text shown in the editor.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Output - {model_name}")
        dialog.setMinimumSize(720, 520)
        layout = QVBoxLayout(dialog)
        editor = QTextEdit(dialog)
        editor.setAcceptRichText(False)
        editor.setPlainText(content)
        layout.addWidget(editor)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Copy")
        buttons.accepted.connect(lambda: QApplication.clipboard().setText(editor.toPlainText()))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    @Slot(str)
    def on_save_to_db(self, model_name: str) -> None:
        """Start an asynchronous save of the selected model output.

        Args:
            model_name: Model identifier for the response to save.
        """
        if model_name in self.saving_models or model_name in self.saved_models:
            return

        self.saving_models.add(model_name)
        save_button = self.save_buttons.get(model_name)
        if save_button is not None:
            save_button.setEnabled(False)

        worker = Worker(
            self.save_prompt,
            model_name,
            self.prompt_info,
            progress_callback=True
        )
        worker.signals.result.connect(self.save_prompt_done)
        worker.signals.progress.connect(self.save_prompt_progress)
        worker.signals.error.connect(lambda ex, model=model_name: self.save_prompt_error(model, ex))
        self.threadpool.start(worker)

    def save_prompt(
            self,
            progress_callback: typing.Callable[[str], None],
            model_name: str,
            prompt_info: dict
    ) -> dict[str, typing.Any]:
        """Persist prompt metadata and the selected model response.

        Args:
            progress_callback: Worker signal used to report save progress.
            model_name: Model identifier for the response to save.
            prompt_info: Prompt metadata and model outputs.

        Returns:
            Save result payload with the model name and created/skipped state.

        Raises:
            Exception: Re-raises database or title-generation failures that
                should fail the save operation. Title generation itself has a
                local fallback and should not normally raise.
        """
        try:
            progress_callback.emit(f"Creating history title for model: {model_name}")
            model_output = prompt_info["prompt_result"][model_name]
            title = self.generate_history_title(model_name, model_output)

            progress_callback.emit(f"Saving prompt for model: {model_name}")

            with self.save_lock:
                with get_db_session() as session:
                    try:
                        session.begin()  # Begin a new transaction

                        if self.prompt_id is None:
                            # Save prompt
                            prompt_id = PromptRepository.add_prompt(
                                session=session,
                                system_instruction=prompt_info["prompt_data"].get("system_instruction", ""),
                                guidance_prompt=prompt_info["prompt_data"].get("guidance_prompt", ""),
                                input_data=self.prompt_info["prompt_input"],
                                capture_mode=prompt_info["prompt_data"].get("capture_mode", ""),
                                title=title,
                            )
                            self.prompt_id = prompt_id

                        progress_callback.emit("Prompt saved, now saving response...")

                        # Save response
                        _, response_created = PromptRepository.get_or_add_response(
                            session=session,
                            prompt_id=self.prompt_id,
                            model_name=model_name,
                            model_output=model_output,
                        )

                        session.commit()
                        if response_created:
                            progress_callback.emit("Prompt and response saved successfully.")
                            return {
                                "model_name": model_name,
                                "created": True,
                                "message": f"{model_name} saved",
                            }

                        progress_callback.emit("Response was already saved; skipped duplicate row.")
                        return {
                            "model_name": model_name,
                            "created": False,
                            "message": f"{model_name} already saved",
                        }

                    except Exception as inner_error:
                        session.rollback()
                        progress_callback.emit(f"❌ Rolled back due to error: {inner_error}")
                        raise inner_error

        except Exception as e:
            progress_callback.emit(f"🔥 Error saving prompt: {e}")
            raise

    def generate_history_title(self, model_name: str, model_output: str) -> str:
        """Generate a display title for a saved model output.

        Args:
            model_name: Model to use for the title-generation call.
            model_output: Output text being saved.

        Returns:
            Clean title generated by the model, or a local fallback title.
        """
        try:
            CredentialStore.hydrate_environment()
            llm = run_async(LLM.create(
                model_name,
                system_instruction=(
                    "Create concise titles for saved notes. Return only the title, "
                    "with no quotes, no markdown, and no trailing punctuation."
                ),
            ))
            prompt = (
                "Create a clear title, 4 to 8 words, for this model output:\n\n"
                f"{model_output[:6000]}"
            )
            title = str(run_async(llm(prompt))).strip()
            return self.clean_history_title(title) or self.fallback_history_title(model_output)
        except Exception as error:
            print(f"Error generating history title: {error}")
            return self.fallback_history_title(model_output)

    @staticmethod
    def clean_history_title(title: str) -> str:
        """Normalize an LLM-generated history title.

        Args:
            title: Raw title returned by an LLM.

        Returns:
            Clean, single-line title limited for display.
        """
        title = re.sub(r"^#+\s*", "", title.strip())
        title = title.strip("\"'`“”‘’ \n\t")
        title = re.sub(r"\s+", " ", title)
        title = title.rstrip(".:;")
        return title[:90].strip()

    @staticmethod
    def fallback_history_title(model_output: str) -> str:
        """Create a local fallback title from model output.

        Args:
            model_output: Output text being saved.

        Returns:
            Short title derived from the first sentence or a generic fallback.
        """
        text = re.sub(r"```.*?```", " ", model_output, flags=re.DOTALL)
        text = re.sub(r"[*_#>`\\-]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return "Saved Model Output"
        sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
        words = sentence.split()[:8]
        title = " ".join(words).rstrip(".:;")
        return title[:90] or "Saved Model Output"


    def save_prompt_done(self, result: dict[str, typing.Any]) -> None:
        """Show a success message after the worker saves output.

        Args:
            result: Worker result payload.
        """
        model_name = str(result["model_name"])
        self.saving_models.discard(model_name)
        self.saved_models.add(model_name)
        save_button = self.save_buttons.get(model_name)
        if save_button is not None:
            save_button.setToolTip("Already saved")

        message = str(result["message"])
        print(f"Done: {message}")
        QMessageBox.information(
            self,
            "Success",
            message,
            QMessageBox.StandardButton.Ok
        )

    def save_prompt_error(self, model_name: str, error: tuple[type[BaseException], BaseException, str]) -> None:
        """Restore the save button and show database save failures.

        Args:
            model_name: Model identifier whose save failed.
            error: Exception details emitted by the save worker.
        """
        self.saving_models.discard(model_name)
        save_button = self.save_buttons.get(model_name)
        if save_button is not None:
            save_button.setEnabled(True)
        _, value, _ = error
        QMessageBox.critical(
            self,
            "Save Failed",
            f"Could not save {model_name}: {value}",
            QMessageBox.StandardButton.Ok,
        )


    def save_prompt_progress(self, progress: str) -> None:
        """Log save progress from the worker thread.

        Args:
            progress: Progress message emitted by the worker.
        """
        print(f"⏳ Progress: {progress}")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    sample_prompt = {
        "prompt_result": {
            "GPT-4": "The capital of France is Paris.",
            "Gemini Pro": "Paris is the capital of France."
        }
    }
    dialog = OutputDialog(prompt_info=sample_prompt)
    dialog.show()
    sys.exit(app.exec())
