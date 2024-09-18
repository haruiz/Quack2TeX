from PySide6.QtCore import Qt, Property, QThreadPool, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel, QMenu

from quack2tex.resources import resources_rc  # noqa: F401


class ModelPicker(QWidget):
    """
    A widget that allows the user to select a model
    """
    on_loaded_models = Signal()

    def __init__(self, parent=None):
        super(ModelPicker, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.thread_pool = QThreadPool()

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)

        self.selected_models_label = QLabel()
        self.layout.addWidget(self.list_widget)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def set_data(self, models):
        """
        Load the models
        :return:
        """
        for model in models:
            model_item = QListWidgetItem(model.display_name)
            model_item.setData(Qt.UserRole, model.name)
            if model.client == "ollama":
                model_item.setIcon(QIcon(":/icons/ollama.png"))
            elif model.client == "google":
                model_item.setIcon(QIcon(":/icons/gemini.png"))
            elif model.client == "openai":
                model_item.setIcon(QIcon(":/icons/openai.png"))
            self.list_widget.addItem(model_item)

    def get_selected_models(self):
        """
        Get the selected models
        :return:
        """
        if not self.list_widget.selectedItems():
            return ""
        return ",".join([item.data(Qt.UserRole) for item in self.list_widget.selectedItems()])

    def set_selected_models(self, models: str):
        """
        Set the selected models
        :param models: the models to select
        :return:
        """
        models_list = models.split(",") if models else []
        for item in self.list_widget.findItems("", Qt.MatchContains):
            if item.data(Qt.UserRole) in models_list:
                item.setSelected(True)

    models = Property(str, get_selected_models, set_selected_models)

    def open_context_menu(self, position):
        """
        Open the context menu
        :param position: the position to open the context menu
        :return:
        """
        context_menu = QMenu()
        action = context_menu.addAction("clear selection")
        action.triggered.connect(lambda: self.list_widget.clearSelection())
        context_menu.exec_(self.mapToGlobal(position))


    def on_selection_changed(self):
        """
        Handler for when the selection changes
        :return:
        """
        selected_models = [item.data(Qt.UserRole) for item in self.list_widget.selectedItems()]
        self.selected_models_label.setText(', '.join(selected_models))
        self.selected_models_label.adjustSize()
        self.layout.addWidget(self.selected_models_label)