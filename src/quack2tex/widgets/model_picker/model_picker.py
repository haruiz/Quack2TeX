from quack2tex.pyqt import (
    Qt, Property, QThreadPool, Signal, QIcon, QListWidget, QListWidgetItem,
    QWidget, QVBoxLayout, QLabel, QMenu
)
from quack2tex.resources import *  # noqa: F401


class ModelPicker(QWidget):
    """
    A widget that allows the user to select a model.
    """
    on_loaded_models = Signal()

    def __init__(self, parent=None):
        super(ModelPicker, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.thread_pool = QThreadPool()

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)

        self.selected_models_label = QLabel()
        self.layout.addWidget(self.list_widget)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def set_data(self, models):
        """
        Load the models into the list widget.
        """
        icons = {
            "ollama": QIcon(":/icons/ollama.png"),
            "google": QIcon(":/icons/google.png"),
            "openai": QIcon(":/icons/openai.png"),
            "anthropic": QIcon(":/icons/anthropic.png"),
            "groq": QIcon(":/icons/groq.png"),
        }
        for model in models:
            model_item = QListWidgetItem(model.display_name)
            model_item.setData(Qt.ItemDataRole.UserRole, model.name)
            if model.client in icons:
                model_item.setIcon(icons[model.client])
            self.list_widget.addItem(model_item)

    def get_selected_models(self):
        """
        Get the selected models.
        """
        if not self.list_widget.selectedItems():
            return ""
        return ",".join([item.data(Qt.ItemDataRole.UserRole) for item in self.list_widget.selectedItems()])

    def set_selected_models(self, models: str):
        """
        Set the selected models.
        :param models: The models to select.
        """
        models_list = models.split(",") if models else []
        for item in self.list_widget.findItems("", Qt.MatchFlag.MatchContains):
            if item.data(Qt.ItemDataRole.UserRole) in models_list:
                item.setSelected(True)

    models = Property(str, get_selected_models, set_selected_models)

    def open_context_menu(self, position):
        """
        Open the context menu at the specified position.
        :param position: The position to open the context menu.
        """
        context_menu = QMenu()
        action = context_menu.addAction("Clear selection")
        action.triggered.connect(lambda: self.list_widget.clearSelection())
        context_menu.exec(self.mapToGlobal(position))

    def on_selection_changed(self):
        """
        Handler for when the selection changes.
        """
        selected_models = [
            item.data(Qt.ItemDataRole.UserRole) for item in self.list_widget.selectedItems()
        ]
        self.selected_models_label.setText(', '.join(selected_models))
        self.selected_models_label.adjustSize()
        self.layout.addWidget(self.selected_models_label)
