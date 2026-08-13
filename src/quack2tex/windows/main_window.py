import typing
import asyncio
from datetime import datetime

from PIL.Image import Image as PILImage
from tqdm import tqdm

from modihub.llm import LLM
from quack2tex.preferences import Preferences
from quack2tex.repository import MenuItemRepository, PromptRepository
from quack2tex.repository.db.sync_session import get_db_session
from quack2tex.pyqt import (
    Qt,
    QApplication,
    QPoint,
    QTimer,
    QThreadPool,
    QMainWindow,
    QMessageBox,
    QShortcut,
    QKeySequence,
)
from quack2tex.utils import GuiUtils, Worker, work_exception, LibUtils, run_async
from quack2tex.widgets import DuckMenu
from .ouput_dialog import OutputDialog
from .command_palette import CommandPalette
from .screen_capture import ScreenCaptureWindow
from .screenshot_preview_dialog import ScreenshotPreviewDialog
from quack2tex.windows.setting_window.settings_window import SettingsWindow
from quack2tex.widgets import PromptDialog
from ..widgets.audio_recorder import AudioRecorderDialog


class MainWindow(QMainWindow):
    """
    Main application window.
    """

    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("QMainWindow { background: transparent; }")

        self.menu = DuckMenu()

        self.menu.build_menu()
        self.menu.on_hold.connect(self.on_hold_handler)
        self.menu.item_clicked.connect(self.handle_menu_item_click)
        self.setCentralWidget(self.menu)
        self.threadpool = QThreadPool()
        self.last_prompt_info = None

        # drag and drop variables
        self.is_moving = False
        self.offset = None

        self.command_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.command_palette_shortcut.activated.connect(self.open_command_palette)
        self._launch_present_attempts = 0

    def present_on_launch(self) -> None:
        """
        Bring the floating menu into view after its asynchronous menu build.
        """
        self._launch_present_attempts = 0
        self._present_when_menu_ready()

    def _present_when_menu_ready(self) -> None:
        root_item = self.menu.root_item() if self.menu.root_item else None
        if root_item is None and self._launch_present_attempts < 20:
            self._launch_present_attempts += 1
            QTimer.singleShot(100, self._present_when_menu_ready)
            return

        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            x = available.right() - self.width() - 32
            y = available.top() + 48
            self.move(QPoint(max(available.left(), x), max(available.top(), y)))

        self.show()
        self.raise_()
        self.activateWindow()

    def on_hold_handler(self):
        """
        Handle the on-hold event.
        :return:
        """
        self.handle_menu_item_click(self.menu.root_item().data)

    def handle_menu_item_click(self, data):
        """
        Handle the menu item click event.
        :param data:
        :return:
        """
        menu_item_action = data.get("action", None)
        menu_item_data = data.get("tag", None)
        if menu_item_action == "exit":
            self.close()
        elif menu_item_action == "settings":
            self.open_settings()
        elif menu_item_action == "history":
            self.open_settings(show_history=True)
        elif menu_item_action == "command_palette":
            self.open_command_palette()
        elif menu_item_action == "pomodoro":
            self.toggle_pomodoro()
        elif menu_item_data:
            self.run_menu_item(menu_item_data)

    def open_settings(self, show_history: bool = False) -> None:
        """
        Open settings and optionally focus the history tab.
        """
        w = SettingsWindow()
        w.on_settings_changed.connect(self.menu.build_menu)
        if show_history:
            w.show_history()
        was_visible = self.isVisible()
        self.hide()
        try:
            w.exec()
        finally:
            if was_visible:
                self.show()
                self.raise_()

    def run_menu_item(self, menu_item_data) -> None:
        """
        Run a configured prompt menu item.
        """
        capture_mode = menu_item_data.capture_mode
        prompt_data = {
            "name": menu_item_data.name,
            "system_instruction": menu_item_data.system_instruction,
            "guidance_prompt": menu_item_data.guidance_prompt,
            "models": menu_item_data.models,
            "capture_mode": capture_mode
        }

        not_models_selected = menu_item_data.models is None or menu_item_data.models == ""
        no_capture_mode = capture_mode is None or capture_mode == ""

        if any([not_models_selected, no_capture_mode]):
            GuiUtils.show_error("Select at least one model and capture mode before running this prompt.")
            return

        if capture_mode == "screen":
            self.start_screen_capture(prompt_data)
        elif capture_mode == "clipboard":
            self.start_clipboard_text_capture(prompt_data)
        elif capture_mode == "text":
            self.start_text_prompt_capture(prompt_data)
        elif capture_mode == "voice":
            self.start_voice_prompt_capture(prompt_data)
        else:
            self.make_prompt_request(prompt_data, prompt_input="")

    def open_command_palette(self) -> None:
        """
        Open searchable command palette for actions and configured prompts.
        """
        commands = [
            {"label": "Open Settings", "action": "settings"},
            {"label": "Open Recent History", "action": "history"},
            {"label": "pomodoro", "action": "pomodoro"},
        ]
        for name, preset in Preferences.presets().items():
            commands.append({
                "label": f"Preset: {name}",
                "action": "preset",
                "preset": preset,
            })

        with get_db_session() as session:
            for item in MenuItemRepository.fetch_tree_data(session):
                self.add_palette_menu_items(commands, item)
            recent_prompts = PromptRepository.get_all_prompts(session)[:8]
            for prompt in recent_prompts:
                label = prompt.title or prompt.guidance_prompt or prompt.system_instruction or "Recent Prompt"
                commands.append({
                    "label": f"History: {label[:80]}",
                    "action": "history",
                })

        palette = CommandPalette(commands, self)
        if palette.exec() and palette.selected_command:
            self.run_command(palette.selected_command)

    def add_palette_menu_items(self, commands: list[dict], menu_item) -> None:
        if menu_item.guidance_prompt and menu_item.system_instruction:
            commands.append({
                "label": f"Prompt: {menu_item.name}",
                "action": "menu_item",
                "item": menu_item,
            })
        for child in menu_item.children:
            self.add_palette_menu_items(commands, child)

    def run_command(self, command: dict) -> None:
        action = command.get("action")
        if action == "settings":
            self.open_settings()
        elif action == "history":
            self.open_settings(show_history=True)
        elif action == "menu_item":
            self.run_menu_item(command["item"])
        elif action == "preset":
            self.run_preset(command["preset"])
        elif action == "pomodoro":
            self.toggle_pomodoro()

    def toggle_pomodoro(self) -> None:
        self.menu.start_pomodoro_timer()

    def run_preset(self, preset: dict) -> None:
        prompt_data = {
            "name": "Preset",
            "system_instruction": "You are a helpful assistant.",
            "guidance_prompt": "Process the captured input clearly and concisely.",
            "models": preset.get("models", ""),
            "capture_mode": preset.get("capture_mode", "clipboard"),
        }
        if not prompt_data["models"]:
            GuiUtils.show_error("Configure models for this preset in Preferences before running it.")
            return
        if prompt_data["capture_mode"] == "screen":
            self.start_screen_capture(prompt_data)
        elif prompt_data["capture_mode"] == "text":
            self.start_text_prompt_capture(prompt_data)
        else:
            self.start_clipboard_text_capture(prompt_data)


    def start_text_prompt_capture(self, prompt_data):
        """
        Start the text prompt capture process
        :param prompt_data:
        :return:
        """
        dialog = PromptDialog(self)
        # Position it bottom-centered relative to the main window
        # parent_geometry = self.geometry()
        # dialog_size = dialog.sizeHint()  # get dialog's preferred size
        # x = parent_geometry.x() + (parent_geometry.width() - dialog_size.width()) // 2
        # y = parent_geometry.y() + parent_geometry.height() - dialog_size.height() + 80  # 10px padding from bottom
        # dialog.move(x, y)

        if dialog.exec():  # If user clicks OK
            prompt = dialog.get_prompt()
            if prompt:
                self.make_prompt_request(prompt_data, prompt_input=prompt)
            else:
                QMessageBox.warning(None, "Empty Prompt", "No prompt was captured.")

    def start_voice_prompt_capture(self, prompt_data):
        """
        Start the voice prompt capture process
        :param prompt_data:
        :return:
        """
        lib_home_dir = LibUtils.get_lib_home()
        recording_settings_file = lib_home_dir.joinpath("recording_settings.json")
        recording_audio_file = lib_home_dir.joinpath("recording_audio.wav")

        dialog = AudioRecorderDialog(
            self,
            recording_settings_file=str(recording_settings_file),
            recording_audio_file=str(recording_audio_file)
        )

        if dialog.exec():  # If user clicks OK
            transcribed_text = dialog.transcribed_text
            if transcribed_text:
                self.make_prompt_request(prompt_data, prompt_input=transcribed_text)


    def pick_screen_region(self):
        """
        Pick the screen region
        :return:
        """
        screen_capture = ScreenCaptureWindow()
        monitor_geometry = GuiUtils.get_current_monitor_geometry(self)
        screen_capture.setGeometry(monitor_geometry)
        screen_capture.exec()
        return screen_capture.selected_region



    def start_screen_capture(self, prompt_data):
        """
        Start the screen capture process
        :param prompt_data:
        :return:
        """
        monitor_index = GuiUtils.get_current_monitor_index(self)
        screen_region = self.pick_screen_region()
        if screen_region:
            @work_exception
            def do_work():
                """
                Perform the screen capture
                :return:
                """
                return GuiUtils.get_screen_capture_image(screen_region, monitor_index)
            def done(result):
                """
                Handle the completion of the screen capture
                :param result:
                :return:
                """
                screen_capture, error = result
                if error:
                    GuiUtils.show_error(str(error))
                    return
                preview_dialog = ScreenshotPreviewDialog(screen_capture, self)
                if not preview_dialog.exec():
                    return
                self.make_prompt_request(prompt_data, prompt_input=screen_capture)
            worker = Worker(do_work)
            worker.signals.result.connect(done)
            self.threadpool.start(worker)

    def start_clipboard_text_capture(self, prompt_data):
        """
        Start the clipboard text capture process
        :param prompt_data:
        :return:
        """
        clipboard_text = GuiUtils.get_clipboard_text()
        if clipboard_text is None:
            GuiUtils.show_error("No text copied to clipboard.")
            return
        self.make_prompt_request(prompt_data, prompt_input=clipboard_text)

    @work_exception
    def make_prompt_request_do_work(self, prompt_data: dict, prompt_input: typing.Union[str,PILImage]):
        """
        Start the prompt data capture process
        :param prompt_data:
        :param prompt_input:
        :param kwargs:
        :return:
        """
        prompt_result = self.process_prompt_request(prompt_data, prompt_input)
        return {
            "prompt_data": prompt_data,
            "prompt_input": prompt_input,
            "prompt_result": prompt_result
        }
    def make_prompt_request_done(self, result):
        """
        Handle the completion of the screen capture and description generation
        :param result:
        :return:
        """
        prompt_info, error = result
        self.menu.hide_loading_indicator()
        if error:
            GuiUtils.show_error(str(error))
            return
        self.last_prompt_info = prompt_info
        self.create_output_dialog(prompt_info)

    def make_prompt_request(self, prompt_data: dict, prompt_input: typing.Union[str,PILImage]):
        """
        Start the prompt data capture process
        :param prompt_data:
        :param prompt_input:
        :param kwargs:
        :return:
        """
        self.menu.show_loading_indicator()

        worker = Worker(self.make_prompt_request_do_work, prompt_data, prompt_input)
        worker.signals.result.connect(self.make_prompt_request_done)
        self.threadpool.start(worker)

    def create_output_dialog(self, prompt_info: dict):
        """
        Create an output window
        :param text:
        :return:
        """
        dialog = OutputDialog(prompt_info, parent=self)
        dialog.retry_requested.connect(self.retry_prompt_with_model)
        dialog.setWindowTitle("Output")
        dialog.adjustSize()
        GuiUtils.move_window_to_center(dialog)
        dialog.activateWindow()
        dialog.exec()

    def retry_prompt_with_model(self, model_name: str) -> None:
        if not self.last_prompt_info:
            return
        prompt_data = dict(self.last_prompt_info["prompt_data"])
        prompt_data["models"] = model_name
        self.make_prompt_request(prompt_data, self.last_prompt_info["prompt_input"])

    @staticmethod
    async def call_llm(model, system_instruction, multimodal_prompt):
        """
        Standalone function to call the language model
        :param model:
        :param system_instruction:
        :param multimodal_prompt:
        :return:
        """
        llm = await LLM.create(model, system_instruction=system_instruction)
        return await llm(multimodal_prompt)


    def process_prompt_request(self, prompt_data: dict, prompt_input:  typing.Union[str,PILImage]) -> dict:
        """
        Call the language model
        :param prompt_data:
        :param prompt_input:
        :return:
        """
        return run_async(self.process_prompt_request_async(prompt_data, prompt_input))

    async def process_prompt_request_async(self, prompt_data: dict, prompt_input: typing.Union[str,PILImage]) -> dict:
        """
        Call the language model using ModiHub's async API.
        :param prompt_data:
        :param prompt_input:
        :return:
        """
        models = prompt_data.get("models")
        system_instruction = self.expand_prompt_variables(prompt_data.get("system_instruction"), prompt_input)
        guidance_prompt = self.expand_prompt_variables(prompt_data.get("guidance_prompt"), prompt_input)
        multimodal_prompt = [guidance_prompt, prompt_input]

        models  = models.split(",") if models else []
        results = {}

        async def call_model(model: str) -> tuple[str, str]:
            try:
                response = await self.call_llm(model, system_instruction, multimodal_prompt)
            except Exception as e:
                response = f"Error by running inference on model {model}: {e}"
            return model, response

        tasks = [
            call_model(model)
            for model in models
        ]
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            model_name, response = await task
            results[model_name] = response
        return results

    def expand_prompt_variables(self, text: str, prompt_input: typing.Union[str, PILImage]) -> str:
        """
        Expand lightweight prompt variables before dispatching to models.
        """
        if text is None:
            return ""
        now = datetime.now()
        values = {
            "clipboard": GuiUtils.get_clipboard_text() or "",
            "selected_text": GuiUtils.get_clipboard_text() or "",
            "date": now.strftime("%Y-%m-%d"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "app_name": "Quack2TeX",
            "input": prompt_input if isinstance(prompt_input, str) else "",
        }
        for key, value in values.items():
            text = text.replace("{" + key + "}", str(value))
        return text



    def mousePressEvent(self, event):
        """
        Triggered when the user presses the mouse button.
        :param event:
        :return:
        """
        if (
                event.button() == Qt.MouseButton.LeftButton and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.is_moving = True
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """
        Triggered when the user moves the mouse.
        :param event:
        :return:
        """
        if self.is_moving and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.offset
            self.move(new_pos)
            self.menu.position_loading_indicator()
            self.menu.position_pomodoro_timer()

    def moveEvent(self, event):
        """
        Keep floating overlays attached when the window moves by any path.
        """
        super().moveEvent(event)
        if hasattr(self, "menu"):
            self.menu.position_loading_indicator()
            self.menu.position_pomodoro_timer()

    def mouseReleaseEvent(self, event):
        """
        Triggered when the user releases the mouse button.
        :param event:
        :return:
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_moving = False

    def closeEvent(self, event):
        """
        Close detached overlays with the main window.
        """
        if hasattr(self, "menu") and hasattr(self.menu, "pomodoro_timer"):
            self.menu.pomodoro_timer.close()
        super().closeEvent(event)
