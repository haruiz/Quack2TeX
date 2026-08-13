from typing import Any

from quack2tex import LLM
from quack2tex.enums import CaptureMode
from quack2tex.utils import GuiUtils, Worker, work_exception, run_async
from quack2tex.widgets import FileUploader, ModelPicker, PromptInput
from quack2tex.pyqt import (
    QDialog, QVBoxLayout, QFormLayout, QTextEdit, QSizePolicy,
    QDialogButtonBox, QComboBox, Qt, QObject, Signal, QLabel,
    QThreadPool, Property, QScrollArea, QWidget
)


class CaptureModeComboBox(QComboBox):
    """
    A combo box for selecting the capture mode.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItem("Select Capture Mode", userData=None)
        for mode in CaptureMode:
            self.addItem(mode.value, userData=mode.value)

    def get_capture_mode(self) -> str:
        return self.currentData(Qt.ItemDataRole.UserRole)

    def set_capture_mode(self, mode: str) -> None:
        for i in range(self.count()):
            if self.itemData(i, Qt.ItemDataRole.UserRole) == mode:
                self.setCurrentIndex(i)
                break

    capture_mode = Property(str, get_capture_mode, set_capture_mode)


class MenuItemForm(QDialog, QObject):
    """
    A form dialog for editing or creating a menu item.
    """
    name = GuiUtils.bind("txt_name", "plainText", str)
    icon = GuiUtils.bind("file_icon_uploader", "file_path", str)
    system_instruction = GuiUtils.bind("txt_system_instructions", "plainText", str)
    guidance_prompt = GuiUtils.bind("txt_guidance_prompt", "plainText", str)
    models = GuiUtils.bind("list_model_picker", "models", str)
    capture_mode = GuiUtils.bind("cbx_capture_mode", "capture_mode", str)

    on_widget_loaded = Signal(dict)

    def __init__(self, initial_values=None, parent=None):
        super().__init__(parent)
        self.setObjectName("menuItemForm")
        self.setWindowTitle("Edit Menu Item")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setMinimumSize(1120, 760)

        self.thread_pool = QThreadPool()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(14)

        self.loading_label = QLabel("Loading data...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.loading_label)

        self.on_widget_loaded.connect(self.on_widget_loaded_handler)
        self.initial_values = initial_values
        self.load_form()

    @property
    def form_values(self) -> dict:
        return {
            "name": self.name,
            "icon": self.icon,
            "system_instruction": self.system_instruction,
            "guidance_prompt": self.guidance_prompt,
            "models": self.models,
            "capture_mode": self.capture_mode
        }

    @form_values.setter
    def form_values(self, data: dict):
        self.name = data.get("name", "")
        self.icon = data.get("icon", "")
        self.system_instruction = data.get("system_instruction", "")
        self.guidance_prompt = data.get("guidance_prompt", "")
        self.models = data.get("models", [])
        self.capture_mode = data.get("capture_mode", None)


    def load_form(self) -> None:
        @work_exception
        def do_work() -> dict[str, Any]:
            return {"models": run_async(LLM.available_models())}

        def done(result):
            data, error = result
            if error:
                GuiUtils.show_error(error)
            else:
                self.on_widget_loaded.emit(data)

        worker = Worker(do_work)
        worker.signals.result.connect(done)
        self.thread_pool.start(worker)

    def on_widget_loaded_handler(self, form_data: dict) -> None:
        self.loading_label.hide()
        self.build_form(form_data)
        if self.initial_values:
            self.form_values = self.initial_values


    def build_form(self, form_data: dict) -> None:
        form_container = QWidget(self)
        form_container.setObjectName("menuItemFormContent")
        form_layout = QFormLayout()
        form_container.setLayout(form_layout)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(22)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self.txt_name = self._create_text_edit("txt_name", "Enter menu item name...", height=44)
        form_layout.addRow("Name:", self.txt_name)

        self.file_icon_uploader = FileUploader(self, file_filter="Images (*.png *.jpg *.jpeg)")
        self.file_icon_uploader.setObjectName("file_icon_uploader")
        self.file_icon_uploader.file_path_edit.setPlaceholderText("Select icon file...")
        self._set_expandable(self.file_icon_uploader)
        form_layout.addRow("Icon:", self.file_icon_uploader)

        system_tooltip = (
            "System Prompt defines the assistant's role, tone, and rules. "
            "It stays stable across inputs for this menu action."
        )
        self.txt_system_instructions = self._create_prompt_edit(
            "txt_system_instructions",
            "Enter system instructions...",
            system_tooltip,
        )
        form_layout.addRow(
            self._create_label("System Prompt:", system_tooltip),
            self.txt_system_instructions,
        )

        guidance_tooltip = (
            "Guidance Prompt is the task instruction applied to the captured input, "
            "such as what to rewrite, summarize, extract, or convert."
        )
        self.txt_guidance_prompt = self._create_prompt_edit(
            "txt_guidance_prompt",
            "Enter guidance prompt...",
            guidance_tooltip,
        )
        form_layout.addRow(
            self._create_label("Guidance Prompt:", guidance_tooltip),
            self.txt_guidance_prompt,
        )

        self.list_model_picker = ModelPicker(self)
        self.list_model_picker.setObjectName("list_model_picker")
        self.list_model_picker.set_data(form_data["models"])
        self.list_model_picker.setFixedHeight(216)
        self._set_expandable(self.list_model_picker, vertical=False)
        form_layout.addRow("Select Models:", self.list_model_picker)

        self.cbx_capture_mode = CaptureModeComboBox(self)
        self.cbx_capture_mode.setFixedHeight(42)
        self.cbx_capture_mode.setObjectName("cbx_capture_mode")
        self._set_expandable(self.cbx_capture_mode)
        form_layout.addRow("Capture Mode:", self.cbx_capture_mode)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("menuItemFormScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setWidget(form_container)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setObjectName("menuItemFormButtons")
        buttons.setMinimumHeight(58)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self._configure_tab_order(buttons)
        self.layout.addWidget(scroll_area, 1)
        self.layout.addWidget(buttons, 0)

    def _create_text_edit(self, name: str, placeholder: str, height: int = None) -> QTextEdit:
        text_edit = QTextEdit(self)
        text_edit.setObjectName(name)
        text_edit.setAcceptRichText(False)
        text_edit.setPlaceholderText(placeholder)
        text_edit.setTabChangesFocus(True)
        if height:
            text_edit.setFixedHeight(height)
        self._set_expandable(text_edit, vertical=False)
        return text_edit

    def _create_label(self, text: str, tooltip: str = "") -> QLabel:
        label = QLabel(text, self)
        label.setToolTip(tooltip)
        return label

    def _create_prompt_edit(self, name: str, placeholder: str, tooltip: str = "") -> PromptInput:
        prompt_edit = PromptInput()
        prompt_edit.setFixedHeight(120)
        prompt_edit.text_edit.setFixedHeight(120)
        prompt_edit.btn_enhance_prompt.setFixedSize(58, 48)
        prompt_edit.setObjectName(name)
        prompt_edit.setPlaceholderText(placeholder)
        prompt_edit.setToolTip(tooltip)
        prompt_edit.text_edit.setToolTip(tooltip)
        prompt_edit.text_edit.setTabChangesFocus(True)
        return prompt_edit

    def _set_expandable(self, widget, vertical=True) -> None:
        widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Expanding if vertical else QSizePolicy.Policy.Fixed)

    def _configure_tab_order(self, button_box) -> None:
        self.setTabOrder(self.txt_name, self.file_icon_uploader.file_path_edit)
        self.setTabOrder(self.file_icon_uploader.file_path_edit, self.txt_system_instructions)
        self.setTabOrder(self.txt_system_instructions, self.txt_guidance_prompt)
        self.setTabOrder(self.txt_guidance_prompt, self.list_model_picker)
        self.setTabOrder(self.list_model_picker, self.cbx_capture_mode)
        self.setTabOrder(self.cbx_capture_mode, button_box)

    def accept(self) -> None:
        if not self.name:
            GuiUtils.show_error("Name and icon are required.")
            return
        super().accept()
