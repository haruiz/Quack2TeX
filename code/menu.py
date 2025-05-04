import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QPropertyAnimation
)
from PyQt6.QtGui import (
    QPainter, QColor, QMouseEvent, QMovie, QFont
)


class MenuItem(QWidget):
    BASE_SIZE = 80
    SIZE_DECREASE = 0.5

    def __init__(self, label, level=0, parent=None):
        super().__init__(parent)
        self.label = label
        self.level = level
        self.children = []
        self.expanded = False
        self.animations = []

        scale = self.SIZE_DECREASE ** self.level
        size = int(self.BASE_SIZE * scale)
        self.setFixedSize(size, size)
        self.setMouseTracking(True)

        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.on_long_press)

        self.holding = False
        self.drag_start_pos = None

        self.mic_label = QLabel(self)
        self.mic_label.setGeometry(self.width() // 4, self.height() // 4, self.width() // 2, self.height() // 2)
        self.mic_label.setVisible(False)
        self.mic_movie = QMovie("../loading.gif")  # Ensure this exists in the same folder
        self.mic_label.setMovie(self.mic_movie)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 150, 255, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 8 + max(0, 3 - self.level), QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.label)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.holding = True
            self.long_press_timer.start(600)
            self.drag_start_pos = event.globalPosition().toPoint()
            self.parent().start_drag(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.parent().continue_drag(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.holding = False
        self.long_press_timer.stop()
        self.drag_start_pos = None
        self.parent().end_drag()

        if self.mic_label.isVisible():
            self.mic_label.setVisible(False)
            self.mic_movie.stop()
        else:
            self.toggle_children()

    def mouseDoubleClickEvent(self, event):
        print(f"Opening item: {self.label}")

    def on_long_press(self):
        self.mic_label.setVisible(True)
        self.mic_movie.start()

    def toggle_children(self):
        self.hide_all_others_except_self_and_root()
        if self.expanded:
            self.hide_all_children()
        else:
            angle_step = 360 / max(len(self.children), 1)
            radius = self.width() / 2
            for i, child in enumerate(self.children):
                angle = math.radians(i * angle_step)
                dx = int(radius * math.cos(angle))
                dy = int(radius * math.sin(angle))
                child.move(self.x() + dx, self.y() + dy)
                child.fade_in()
                child.show()
        self.expanded = not self.expanded

    def hide_all_others_except_self_and_root(self):
        for item in self.parent().findChildren(MenuItem):
            if item is not self and item.level != 0:
                item.hide()
                item.expanded = False
                item.hide_all_children()

    def hide_all_children(self):
        for child in self.children:
            child.hide()
            child.hide_all_children()

    def fade_in(self):
        self.setVisible(True)
        self.opacity_effect.setOpacity(0.0)
        anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        self.animations.append(anim)


class FloatingMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Floating Menu")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(300, 300, 1000, 800)

        self.drag_position = None
        self.dragging = False

        self.root_item = MenuItem("AI", level=0, parent=self)
        self.root_item.move(450, 350)

        # Level 1
        chat = MenuItem("Chat", level=1, parent=self)
        tools = MenuItem("Tools", level=1, parent=self)
        vision = MenuItem("Vision", level=1, parent=self)

        # Level 2
        slack = MenuItem("Slack", level=2, parent=self)
        discord = MenuItem("Discord", level=2, parent=self)
        calc = MenuItem("Calc", level=2, parent=self)
        notes = MenuItem("Notes", level=2, parent=self)
        detect = MenuItem("Detect", level=2, parent=self)
        classify = MenuItem("Classify", level=2, parent=self)

        # Level 3
        sci_calc = MenuItem("Sci", level=3, parent=self)
        voice_notes = MenuItem("Voice", level=3, parent=self)
        image_detect = MenuItem("Faces", level=3, parent=self)

        # Level 4
        deep_classify = MenuItem("DeepNet", level=4, parent=self)

        # Nesting
        tools.children.extend([calc, notes])
        calc.children.append(sci_calc)
        notes.children.append(voice_notes)

        chat.children.extend([slack, discord])
        vision.children.extend([detect, classify])
        detect.children.append(image_detect)
        classify.children.append(deep_classify)

        self.root_item.children.extend([chat, tools, vision])

        # Hide all children initially
        for item in self.root_item.children + tools.children + chat.children + vision.children + \
                   calc.children + notes.children + detect.children + classify.children:
            item.hide()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.continue_drag(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.end_drag()

    def start_drag(self, event):
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self.dragging = True

    def continue_drag(self, event):
        if self.dragging and self.drag_position:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)

    def end_drag(self):
        self.dragging = False
        self.drag_position = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingMenu()
    window.show()
    sys.exit(app.exec())
