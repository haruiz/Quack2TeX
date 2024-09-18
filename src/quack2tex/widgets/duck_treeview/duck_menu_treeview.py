from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QSize, QThreadPool,
)
from PySide6.QtWidgets import (
    QTreeView,
    QAbstractItemView,
)


class DuckMenuTreeView(QTreeView):
    """
    A custom QTreeView that displays a tree of items
    """
    def __init__(self):
        super(DuckMenuTreeView, self).__init__()
        self.setIconSize(QSize(24, 24))
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setDropIndicatorShown(True)
        self.thread_pool = QThreadPool()
