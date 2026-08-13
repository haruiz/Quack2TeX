from quack2tex.pyqt import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    Qt,
)


class CommandPalette(QDialog):
    """
    Searchable launcher for menu actions and prompts.
    """

    def __init__(self, commands: list[dict], parent=None):
        super().__init__(parent)
        self.setObjectName("commandPalette")
        self.setWindowTitle("Command Palette")
        self.setMinimumSize(520, 520)
        self.commands = commands
        self.selected_command = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search commands and prompts...")
        self.search.textChanged.connect(self.populate)
        layout.addWidget(self.search)

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.populate()

    def populate(self) -> None:
        query = self.search.text().strip().lower()
        self.list_widget.clear()
        for command in self.commands:
            label = command["label"]
            if query and query not in label.lower():
                continue
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, command)
            self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def accept(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            self.selected_command = item.data(Qt.ItemDataRole.UserRole)
        super().accept()
