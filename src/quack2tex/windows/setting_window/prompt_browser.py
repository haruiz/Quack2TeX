import typing
from io import BytesIO

from PIL import Image
from PyQt6.QtWidgets import QDialog, QSplitter, QPushButton

from quack2tex.pyqt import (
    QModelIndex, QThreadPool, QStandardItem, QStandardItemModel,
    QWidget, QHBoxLayout,
    QVBoxLayout, QFrame, QMouseEvent,
    QLabel,
QCursor,
    QIcon,
    Qt, QImage, QPixmap, QGraphicsView,
    QGraphicsPixmapItem, QPainter, QWheelEvent, QGraphicsScene, QMessageBox,QMenu,QApplication
)
from quack2tex.repository import PromptRepository
from quack2tex.repository.db.sync_session import get_db_session
from quack2tex.repository.models import Prompt, Response
from quack2tex.utils import Worker
from quack2tex.widgets import MarkdownViewer
from quack2tex.windows.setting_window.hoverable_treeview import HoverableTreeView


class ImageDialogViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item: QGraphicsPixmapItem = None


        # Zoom config
        self._scale = 1.0
        self._min_scale = 0.1
        self._max_scale = 5.0
        self._zoom_step = 0.1

    @property
    def pixmap(self):
        return self._pixmap_item.pixmap() if self._pixmap_item else None

    @pixmap.setter
    def pixmap(self, value: QPixmap):
        self._scene.clear()
        self.resetTransform()
        self._scale = 1.0

        self._pixmap_item = QGraphicsPixmapItem(value)
        self._pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self._pixmap_item.setOffset(-value.width() / 2, -value.height() / 2)
        self._scene.addItem(self._pixmap_item)

        # Fit-to-size initial scale
        view_width = self.viewport().width()
        img_width = value.width()
        if img_width > 0:
            initial_scale = min(1.0, view_width / img_width)
            self._scale = initial_scale
            self.scale(self._scale, self._scale)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y() / 120
        if delta == 0:
            return

        factor = 1 + self._zoom_step * delta
        new_scale = self._scale * factor

        if self._min_scale <= new_scale <= self._max_scale:
            self._scale = new_scale
            self.scale(factor, factor)

class PromptDetailsDialog(QDialog):
    """
    Dialog to show prompt details.
    """
    def __init__(self, prompt: Prompt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt Details")
        # self.setWindowOpacity(0.8)
        # self.setWindowFlags(
        #     Qt.WindowType.Popup |
        #     Qt.WindowType.FramelessWindowHint |
        #     Qt.WindowType.WindowStaysOnTopHint |
        #     Qt.WindowType.X11BypassWindowManagerHint
        # )
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        content_frame = QFrame()
        content_frame.setLayout(QVBoxLayout())
        content_frame.layout().setContentsMargins(8, 8, 8, 8)
        if prompt.capture_mode == "screen":
            try:
                image = Image.open(BytesIO(prompt.prompt_input)).convert("RGBA")
                #image.thumbnail((128, 128), Image.LANCZOS)
                data = image.tobytes("raw", "RGBA")
                qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)

                image_viewer = ImageDialogViewer()
                image_viewer.pixmap = pixmap
                content_frame.layout().addWidget(image_viewer)
            except Exception as e:
                content_frame.layout().addWidget(QLabel(f"Image error: {e}"))
        else:
            label = QLabel(prompt.prompt_input.decode("utf-8", errors="replace"))
            label.setWordWrap(True)
            content_frame.layout().addWidget(label)

        self.layout().addWidget(content_frame)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.rect().contains(event.pos()):
            self.close()


class PromptBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Layout
        self.main_layout = QHBoxLayout(self)

        # Right: Toolbox for model outputs
        self.prompt_tree = HoverableTreeView()
        self.prompt_tree.doubleClicked.connect(self.on_tree_item_clicked)
        self.prompt_tree.setHeaderHidden(True)
        self.prompt_tree.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prompt_tree.clicked.connect(self.on_tree_item_clicked)
        self.prompt_model = QStandardItemModel()
        self.prompt_model.setHorizontalHeaderLabels(["Prompt & Responses"])
        self.prompt_tree.setModel(self.prompt_model)
        self.main_layout.addWidget(self.prompt_tree, 2)


        self.right_widget = QFrame()
        self.right_widget_layout = QVBoxLayout(self.right_widget)
        self.right_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.markdown_viewer = MarkdownViewer()
        self.output_viewer_actions = QSplitter()
        self.output_viewer_actions.setOrientation(Qt.Orientation.Horizontal)
        self.output_viewer_actions.setHandleWidth(5)
        self.btn_copy = QPushButton()
        self.btn_copy.setIcon(QIcon(":icons/copy-clipboard.png"))
        self.btn_copy.setToolTip("Copy to clipboard")
        self.btn_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_copy.setFixedSize(40, 40)
        self.btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.markdown_viewer.content))
        self.output_viewer_actions.addWidget(self.btn_copy)

        self.right_widget_layout.addWidget(self.output_viewer_actions)
        self.right_widget_layout.addWidget(self.markdown_viewer)

        self.main_layout.addWidget(self.right_widget, 3)

        # Load prompts from DB
        self.threadpool = QThreadPool()
        self.load_prompts()

    def load_prompts(self):
        """
        Load prompts from the database and populate the prompt list.
        """
        self.worker = Worker(self.do_load_prompts, progress_callback=True)
        self.worker.signals.result.connect(self.on_load_prompts_done)
        self.worker.signals.progress.connect(self.on_load_prompts_progress)
        self.worker.signals.error.connect(lambda ex: print(f"Error: {ex}"))
        self.threadpool.start(self.worker)

    def do_load_prompts(self, progress_callback: typing.Callable[[str], None]) -> typing.List[Prompt]:
        """
        Load prompts from the database.
        :param progress_callback:
        :return:
        """
        progress_callback.emit("Loading prompts...")
        with get_db_session() as session:
            prompts = PromptRepository.get_all_prompts(session)
        return prompts

    def on_load_prompts_done(self, prompts: typing.List[Prompt]) -> None:
        """
        Handle the completion of loading prompts.
        :param prompts:
        :return:
        """
        for prompt in prompts:
            prompt_item = QStandardItem(prompt.guidance_prompt or prompt.system_instruction)
            prompt_item.setEditable(False)
            prompt_item.setSelectable(False)
            prompt_item.setData(prompt, Qt.ItemDataRole.UserRole)
            for response in prompt.responses:  # Access responses directly!
                response_item = QStandardItem(response.model)
                response_item.setEditable(False)
                response_item.setData(response, Qt.ItemDataRole.UserRole)
                prompt_item.appendRow(response_item)
            self.prompt_model.appendRow(prompt_item)

    def on_load_prompts_progress(self, message: str) -> None:
        """
        Update the progress message.
        :param message:
        :return:
        """
        self.setWindowTitle(message)

    def on_tree_item_clicked(self, index: QModelIndex) -> None:
        """
        Handle the click event on the tree item.
        :param index:
        :return:
        """
        item: QStandardItem = self.prompt_model.itemFromIndex(index)
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, Response):
            self.markdown_viewer.content = data.output  # Show response in MarkdownViewer


    def delete_selected_item(self):
        index = self.prompt_tree.currentIndex()
        item = self.prompt_model.itemFromIndex(index)
        if not item:
            QMessageBox.warning(self, "Delete", "No item selected.")
            return

        data = item.data(Qt.ItemDataRole.UserRole)

        if isinstance(data, Prompt):
            confirm = QMessageBox.question(
                self, "Delete Prompt",
                "Are you sure you want to delete this prompt and all associated responses?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                with get_db_session() as session:
                    PromptRepository.delete_prompt(session, data.id)
                self.prompt_model.removeRow(item.row())
        elif isinstance(data, Response):
            confirm = QMessageBox.question(
                self, "Delete Response",
                "Are you sure you want to delete this response?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                with get_db_session() as session:
                    PromptRepository.delete_response(session, data.id)
                parent_item = item.parent()
                parent_item.removeRow(item.row())

    def view_prompt_input(self):
        index = self.prompt_tree.currentIndex()
        item = self.prompt_model.itemFromIndex(index)
        if not item:
            QMessageBox.warning(self, "View Prompt Input", "No item selected.")
            return

        data = item.data(Qt.ItemDataRole.UserRole)

        if isinstance(data, Prompt):
            prompt_details_dialog = PromptDetailsDialog(data, self)
            prompt_details_dialog.exec()


    def contextMenuEvent(self, event):
        index = self.prompt_tree.indexAt(event.pos())
        if index.isValid():
            menu = QMenu(self)
            delete_action = menu.addAction("Delete")
            view_prompt_action = menu.addAction("View Prompt Input")
            action = menu.exec(event.globalPos())
            if action == delete_action:
                self.delete_selected_item()
            elif action == view_prompt_action:
                self.view_prompt_input()



