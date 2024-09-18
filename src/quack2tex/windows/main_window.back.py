import mss
from PIL import Image
from PIL.Image import Image as PILImage
from PySide6 import QtCore
from PySide6.QtCore import Qt, QThreadPool, QPoint
from PySide6.QtWidgets import (
    QMainWindow,
)

from quack2tex.decors import gui_exception
from quack2tex.llm import LLM
from quack2tex.resources import resources_rc  # noqa: F401
from quack2tex.utils import GuiUtils
from quack2tex.utils import Worker
from quack2tex.widgets import DuckFloatingMenu, MarkdownViewer
from quack2tex.windows import ScreenCaptureWindow


class MainWindow(QMainWindow):
    """
    Main application window
    """

    def __init__(self, model_name: str = "models/gemini-1.5-flash-latest"):
        super().__init__()
        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.duck_menu = DuckFloatingMenu()
        self.duck_menu.item_clicked.connect(self.handle_menu_item_click)
        self.threadpool = QThreadPool()
        self.setCentralWidget(self.duck_menu)
        self.drag_pos = QPoint()
        self.model_name = model_name

    @gui_exception
    def handle_menu_item_click(self, item_value, item_data):
        """
        Handle the menu item click
        :param item_value:
        :param item_data:
        :return:
        """
        if item_value == "close":
            self.close()
        elif item_value == "history":
            raise NotImplementedError("History not implemented yet.")
        elif item_data:
            capture_mode = item_data.get("capture_mode")
            if capture_mode == "screen":
                self.start_screen_capture(item_data)
            elif capture_mode == "text":
                self.start_clipboard_text_capture(item_data)



    def call_llm(
        self, prompt_data: PILImage | str , item_data: dict
    ):
        """
        Describe the image
        :param prompt_data: The prompt data (image or text)
        :param item_data: The item data
        :return:
        """
        system_instruction = item_data.get("system_instruction")
        guidance_prompt = item_data.get("guidance_prompt")
        llm = LLM.create(self.model_name, system_instruction=system_instruction)
        prompt = [guidance_prompt, prompt_data]
        return llm(prompt)


    def start_screen_capture(self, item_action_data):
        """
        Start the screen capture process
        :param item_action_data:
        :return:
        """
        monitor_index = GuiUtils.get_current_monitor_index(self)
        screen_region = self.pick_screen_region()
        if screen_region:
            self.start_prompt_data_capture(item_action_data, screen_region=screen_region, monitor_index=monitor_index)


    def start_clipboard_text_capture(self, item_action_data):
        """
        Start the clipboard text capture process
        :param item_action_data:
        :return:
        """
        clipboard_text = GuiUtils.get_clipboard_text()
        if clipboard_text:
            self.start_prompt_data_capture(item_action_data, prompt_input_data=clipboard_text)

    def start_prompt_data_capture(self, item_data, **kwargs):
        """
        Execute the screen capture and description generation
        :param item_data:
        :return:
        """
        self.duck_menu.loading_indicator.show()

        def do_work():
            """
            Perform the screen capture and description generation
            :return:
            """
            try:
                prompt_input_data = kwargs.get("prompt_input_data")
                if not prompt_input_data:
                    screen_region = kwargs.get("screen_region")
                    monitor_index = kwargs.get("monitor_index")
                    prompt_input_data = self.capture_screen_region(screen_region, monitor_index)
                prompt_llm_output = self.call_llm(prompt_input_data, item_data)
                return None, (prompt_llm_output, prompt_llm_output)
            except Exception as e:
                return e, None

        def on_complete(result):
            """
            Handle the completion of the screen capture and description generation
            :param result:
            :return:
            """
            self.handle_completion(result)

        worker = Worker(do_work)
        worker.signals.result.connect(on_complete)
        self.threadpool.start(worker)

    def handle_completion(self, result):
        """
        Handle the completion of the screen or clipboard capture and description generation
        :param result:
        :return:
        """
        error, result = result
        self.duck_menu.loading_indicator.close()

        if error:
            GuiUtils.show_error_message(str(error))
        else:
            prompt_input_data, prompt_llm_output = result
            self.show_description_window(prompt_llm_output)

    def show_description_window(self, description):
        """
        Show the description window
        :param description:
        :return:
        """
        viewer = MarkdownViewer()
        viewer.set_content(description)
        self.create_window(viewer, "Output")

    def create_window(self, widget, title):
        """
        Create a new window with the specified widget
        :param widget:
        :param title:
        :return:
        """
        window = QMainWindow(self)
        window.setWindowTitle(title)
        window.setWindowFlags(Qt.Window)
        window.setCentralWidget(widget)
        window.adjustSize()
        GuiUtils.move_window_to_center(window)
        window.activateWindow()
        window.show()

    def pick_screen_region(self):
        """
        Pick the screen region
        :return:
        """
        screen_capture = ScreenCaptureWindow()
        screen_capture.setGeometry(GuiUtils.get_current_monitor_geometry(self))
        screen_capture.exec()
        return screen_capture.selected_region

    @staticmethod
    def capture_screen_region(screen_region, monitor_index):
        """
        Capture the screen region
        :param screen_region:
        :param monitor_index:
        :return:
        """
        # TODO: Add support for multiple monitors and DPI scaling factors

        with mss.mss() as sct:
            monitor = {
                "top": screen_region[1],
                "left": screen_region[0],
                "width": screen_region[2],
                "height": screen_region[3],
            }
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.format = "PNG"
            return img


    def mousePressEvent(self, event):
        """
        Handle the mouse press event
        :param event:
        :return:
        """
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle the mouse move event
        :param event:
        :return:
        """
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
        super().mouseMoveEvent(event)

    def showEvent(self, event):
        """
        Handle the show event
        :param event:
        :return:
        """
        GuiUtils.move_window_to_top_center(self)
        super().showEvent(event)
