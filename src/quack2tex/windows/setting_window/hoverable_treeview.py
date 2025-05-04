from quack2tex.pyqt import (
    QTreeView, QTimer, QModelIndex, Signal
)

class HoverableTreeView(QTreeView):
    hovered = Signal(QModelIndex)
    doubleClicked = Signal(QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(1000)  # 800 ms timeout
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._on_hover_timeout)

        self._last_hovered_index: QModelIndex = QModelIndex()

        self.setMouseTracking(True)  # Required for hover events

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        if index != self._last_hovered_index:
            self._hover_timer.stop()
            self._last_hovered_index = index
            if index.isValid():
                self._hover_timer.start()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_timer.stop()
        self._last_hovered_index = QModelIndex()
        super().leaveEvent(event)

    def _on_hover_timeout(self):
        if self._last_hovered_index.isValid():
            self.hovered.emit(self._last_hovered_index)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        index = self.indexAt(event.pos())
        if index.isValid():
            self.doubleClicked.emit(index)



