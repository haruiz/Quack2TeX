from typing import Any

from PySide6.QtCore import Qt, QObject, QThreadPool, Signal, Property
from PySide6.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QTextEdit, QSizePolicy, QComboBox, QDialogButtonBox, \
    QLabel

from quack2tex import LLM
from quack2tex.utils import GuiUtils, Worker, work_exception
from quack2tex.widgets import FileUploader, ModelPicker


class CaptureModeComboBox(QComboBox):
    """
    A combo box for selecting the capture mode
    """

    def __init__(self, parent=None):
        super(CaptureModeComboBox, self).__init__(parent)
        self.addItem("Select Capture Mode", userData=None)
        self.addItem("Screen", userData="screen")
        self.addItem("Clipboard", userData="clipboard")

    def get_capture_mode(self):
        """
        Get the capture mode
        :return:
        """
        return self.currentData(Qt.UserRole)

    def set_capture_mode(self, mode):
        """
        Set the capture mode
        :param mode:
        :return:
        """
        for i in range(self.count()):
            if self.itemData(i, Qt.UserRole) == mode:
                self.setCurrentIndex(i)
                break

    capture_mode = Property(str, get_capture_mode, set_capture_mode)



class MenuItemForm(QDialog, QObject):
    """
    A custom form for editing menu items
    """
    """
       A dialog for adding a new menu item
       """
    name = GuiUtils.bind("txt_name", "plainText", str)
    icon = GuiUtils.bind("file_icon_uploader", "file_path", str)
    system_instruction = GuiUtils.bind("txt_system_instructions", "plainText", str)
    guidance_prompt = GuiUtils.bind("txt_guidance_prompt", "plainText", str)
    models = GuiUtils.bind("list_model_picker", "models", str)
    capture_mode = GuiUtils.bind("cbx_capture_mode", "capture_mode", str)

    on_widget_loaded = Signal(dict)

    def __init__(self, parent=None):
        super(MenuItemForm, self).__init__(parent)
        self.setWindowTitle("Edit menu item")
        self.setModal(True)

        # Main Layout
        self.layout = QVBoxLayout(self)
        self.setFixedSize(400, 400)

        self.loading_label = QLabel("Loading data...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.on_widget_loaded.connect(self.on_widget_loaded_handler)
        self.layout.addWidget(self.loading_label)
        self.thread_pool = QThreadPool()
        self.form_data = None
        self.load_data()


    def build_form(self, data: dict):
        """
        Create the form
        :return:
        """
        GuiUtils.clear_layout(self.layout)
        # Form Layout
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.txt_name = QTextEdit(self)
        self.txt_name.setFixedHeight(30)
        self.txt_name.setObjectName("txt_name")
        # dont allow rich text
        self.txt_name.setAcceptRichText(False)
        self.txt_name.setPlaceholderText("Enter menu item name...")
        self.txt_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form_layout.addRow("Name:", self.txt_name)

        self.file_icon_uploader = FileUploader(self, file_filter="Images (*.png *.jpg *.jpeg)")
        self.file_icon_uploader.setObjectName("file_icon_uploader")
        self.file_icon_uploader.file_path_edit.setPlaceholderText("Select icon file...")
        self.file_icon_uploader.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addRow("Icon:", self.file_icon_uploader)

        self.txt_system_instructions = QTextEdit(self)
        self.txt_system_instructions.setObjectName("txt_system_instructions")
        self.txt_system_instructions.setAcceptRichText(False)
        self.txt_system_instructions.setPlaceholderText("Enter system instructions...")
        self.txt_system_instructions.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addRow("System Instruction:", self.txt_system_instructions)

        self.txt_guidance_prompt = QTextEdit(self)
        self.txt_guidance_prompt.setObjectName("txt_guidance_prompt")
        self.txt_guidance_prompt.setAcceptRichText(False)
        self.txt_guidance_prompt.setPlaceholderText("Enter guidance prompt...")
        self.txt_guidance_prompt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addRow("Guidance Prompt:", self.txt_guidance_prompt)

        # Model Selection (Multiple Selection)
        self.list_model_picker = ModelPicker(self)
        self.list_model_picker.setObjectName("list_model_picker")
        self.list_model_picker.set_data(data["models"])
        self.list_model_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addRow("Select Models:", self.list_model_picker)

        self.cbx_capture_mode = CaptureModeComboBox(self)
        self.cbx_capture_mode.setObjectName("cbx_capture_mode")
        self.cbx_capture_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addRow("Capture Mode:", self.cbx_capture_mode)

        # Dialog Buttons (OK and Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        form_layout.addRow(button_box)

        # disable tab in the text fields
        self.txt_name.setTabChangesFocus(True)
        self.txt_system_instructions.setTabChangesFocus(True)
        self.txt_guidance_prompt.setTabChangesFocus(True)

        # set tab order
        self.setTabOrder(self.txt_name, self.file_icon_uploader.file_path_edit)
        self.setTabOrder(self.file_icon_uploader.file_path_edit, self.txt_system_instructions)
        self.setTabOrder(self.txt_system_instructions, self.txt_guidance_prompt)
        self.setTabOrder(self.txt_guidance_prompt, self.list_model_picker)
        self.setTabOrder(self.list_model_picker, self.cbx_capture_mode)
        self.setTabOrder(self.cbx_capture_mode, button_box)
        self.setTabOrder(button_box, self.file_icon_uploader.file_path_edit)

        self.layout.addLayout(form_layout)

    def load_data(self):
        """
        Load the models
        """
        @work_exception
        def do_work()-> dict[str, Any]:
            """
            Load the models
            :return:
            """
            data = {"models": LLM.available_models()}
            return data

        def done(result):
            """
            Handler for when the models are loaded
            """
            data, error = result
            if error:
                GuiUtils.show_error(error)
                return

            self.on_widget_loaded.emit(data)


        worker = Worker(do_work)
        worker.signals.result.connect(done)
        self.thread_pool.start(worker)

    def on_widget_loaded_handler(self, data):
        """
        Handler for when the widget is loaded
        """
        self.build_form(data)
        if self.form_data:
            self.name = self.form_data.get("name")
            self.icon = self.form_data.get("icon")
            self.system_instruction = self.form_data.get("system_instruction")
            self.guidance_prompt = self.form_data.get("guidance_prompt")
            self.models = self.form_data.get("models")
            self.capture_mode = self.form_data.get("capture_mode")

    def accept(self):
        """
        Accept the dialog and close it
        """
        if any([not self.name, not self.icon]):
            GuiUtils.show_error("Name and icon are required.")
            return
        return super(MenuItemForm, self).accept()

def main():
    """
    Main function
    :return:
    """
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    form = MenuItemForm()
    form.form_data = {
        "name": "Test",
        "icon": "icon.png",
        "system_instruction": "System Instruction",
        "guidance_prompt": "Guidance Prompt",
        "models": "phi3.5:latest",
        "capture_mode": "clipboard"
    }
    form.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

