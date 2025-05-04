import typing
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from PIL.Image import Image as PILImage
from tqdm import tqdm

from modihub.llm import LLM
from quack2tex.pyqt import (
    Qt,
    QThreadPool,
    QMainWindow,
    QMessageBox,
)
from quack2tex.utils import GuiUtils, Worker, work_exception, LibUtils
from quack2tex.widgets import DuckMenu
from .ouput_dialog import OutputDialog
from .screen_capture import ScreenCaptureWindow
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

        self.menu = DuckMenu()
        self.menu.setFixedSize(400, 400)
        self.menu.build_menu()
        self.menu.on_hold.connect(self.on_hold_handler)
        self.menu.item_clicked.connect(self.handle_menu_item_click)
        self.setCentralWidget(self.menu)
        self.threadpool = QThreadPool()

        # drag and drop variables
        self.is_moving = False
        self.offset = None

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
            w = SettingsWindow()
            w.on_settings_changed.connect(self.menu.build_menu)
            w.exec()
        elif menu_item_data:
            capture_mode = menu_item_data.capture_mode
            prompt_data = {
                "system_instruction": menu_item_data.system_instruction,
                "guidance_prompt": menu_item_data.guidance_prompt,
                "models": menu_item_data.models,
                "capture_mode": capture_mode
            }

            not_models_selected = menu_item_data.models is None or menu_item_data.models == ""
            no_capture_mode = capture_mode is None or capture_mode == ""

            if any([not_models_selected, no_capture_mode]):
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


    def start_text_prompt_capture(self, prompt_data):
        """
        Start the text prompt capture process
        :param prompt_data:
        :return:
        """
        dialog = PromptDialog(self)
        dialog.setMinimumSize(400, 100)# set self as parent
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
        if error:
            GuiUtils.show_error(str(error))
            return
        self.menu.loading_indicator.close()
        self.create_output_dialog(prompt_info)

    def make_prompt_request(self, prompt_data: dict, prompt_input: typing.Union[str,PILImage]):
        """
        Start the prompt data capture process
        :param prompt_data:
        :param prompt_input:
        :param kwargs:
        :return:
        """
        self.menu.loading_indicator.show()

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
        dialog.setWindowTitle("Output")
        dialog.adjustSize()
        GuiUtils.move_window_to_center(dialog)
        dialog.activateWindow()
        dialog.exec()

    @staticmethod
    def call_llm(model, system_instruction, multimodal_prompt):
        """
        Standalone function to call the language model
        :param model:
        :param system_instruction:
        :param multimodal_prompt:
        :return:
        """
        llm = LLM.create(model, system_instruction=system_instruction)
        return llm(multimodal_prompt)


    def process_prompt_request(self, prompt_data: dict, prompt_input:  typing.Union[str,PILImage]) -> dict:
        """
        Call the language model
        :param prompt_data:
        :param prompt_input:
        :return:
        """
        models = prompt_data.get("models")
        system_instruction = prompt_data.get("system_instruction")
        guidance_prompt = prompt_data.get("guidance_prompt")
        multimodal_prompt = [guidance_prompt, prompt_input]

        models  = models.split(",") if models else []
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.call_llm, model, system_instruction, multimodal_prompt): model
                for model in models
            }
            for future in tqdm(as_completed(futures), total=len(futures)):
                model_name = futures[future]
                try:
                    results[model_name] = future.result()
                except Exception as e:
                    results[model_name] = f"Error by running inference on model {model_name}: {e}"
        return results



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

    def mouseReleaseEvent(self, event):
        """
        Triggered when the user releases the mouse button.
        :param event:
        :return:
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_moving = False
