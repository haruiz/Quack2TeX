import typing
import time

from PyQt6.QtWidgets import QMessageBox

from quack2tex.pyqt import (
    QToolBox, QDialog, QVBoxLayout, QWidget, QPushButton,
    QApplication, QIcon, QCursor, Qt, QSplitter, QThreadPool, Slot
)
from quack2tex.repository import PromptRepository
from quack2tex.resources import *  # noqa: F401
from quack2tex.utils import Worker
from quack2tex.widgets import MarkdownViewer
from quack2tex.repository.db.sync_session import get_db_session

class OutputDialog(QDialog):
    """
    A window to display model predictions output with clipboard and save buttons.
    """

    def __init__(self, prompt_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Output Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.threadpool = QThreadPool()
        self.prompt_info = prompt_info
        self.prompt_id = None  # Optional placeholder

        self.toolbox = QToolBox()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.toolbox)

        self.populate_toolbox()


    def populate_toolbox(self):
        prompt_result = self.prompt_info.get("prompt_result", {})
        for model_name, model_output in prompt_result.items():
            self.toolbox.addItem(
                self.create_toolbox_page(model_name, model_output),
                model_name
            )

    def create_toolbox_page(self, model_name: str, model_output: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        viewer = MarkdownViewer()
        viewer.content = model_output

        toolbar = QSplitter(Qt.Orientation.Horizontal)

        btn_copy = self._make_icon_button(":icons/copy-clipboard.png", "Copy to clipboard")
        btn_copy.clicked.connect(lambda _, content=model_output: self.on_copy_text(content))

        btn_save = self._make_icon_button(":icons/save.png", "Save to database")
        btn_save.clicked.connect(lambda _, model=model_name: self.on_save_to_db(model))

        toolbar.addWidget(btn_copy)
        toolbar.addWidget(btn_save)

        layout.addWidget(toolbar)
        layout.addWidget(viewer)
        return widget

    def _make_icon_button(self, icon_path: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedSize(40, 40)
        return btn

    @Slot(str)
    def on_copy_text(self, content: str):
        QApplication.clipboard().setText(content)

    @Slot(str)
    def on_save_to_db(self, model_name: str):
        worker = Worker(
            self.save_prompt,
            model_name,
            self.prompt_info,
            progress_callback=True
        )
        worker.signals.result.connect(self.save_prompt_done)
        worker.signals.progress.connect(self.save_prompt_progress)
        worker.signals.error.connect(lambda ex: print(f"Error: {ex}"))
        self.threadpool.start(worker)

    def save_prompt(
            self,
            progress_callback: typing.Callable[[str], None],
            model_name: str,
            prompt_info: dict
    ) -> str:
        try:
            progress_callback.emit(f"Saving prompt for model: {model_name}")

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
                            capture_mode=prompt_info["prompt_data"].get("capture_mode", "")
                        )
                        self.prompt_id = prompt_id

                    progress_callback.emit("Prompt saved, now saving response...")

                    # Save response
                    PromptRepository.add_response(
                        session=session,
                        prompt_id=self.prompt_id,
                        model_name=model_name,
                        model_output=prompt_info["prompt_result"][model_name]
                    )

                    session.commit()
                    progress_callback.emit("✅ Prompt and response saved successfully.")
                    return "Prompt and response saved"

                except Exception as inner_error:
                    session.rollback()
                    progress_callback.emit(f"❌ Rolled back due to error: {inner_error}")
                    raise inner_error

        except Exception as e:
            progress_callback.emit(f"🔥 Error saving prompt: {e}")
            raise


    def save_prompt_done(self, result: str):
        print(f"✅ Done: {result}")
        QMessageBox.information(
            self,
            "Success",
            "Prompt saved successfully!",
            QMessageBox.StandardButton.Ok
        )


    def save_prompt_progress(self, progress: str):
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
