import math
from pathlib import Path

from quack2tex.pyqt import (
    QApplication,
    QColor,
    QFont,
    QIcon,
    QLabel,
    QPoint,
    QPointF,
    QPainter,
    QPen,
    QPixmap,
    QPropertyAnimation,
    QPushButton,
    QRadialGradient,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QUrl,
    QWidget,
)

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
except Exception:  # pragma: no cover - depends on optional Qt multimedia bindings.
    QAudioOutput = None
    QMediaPlayer = None


class PomodoroTimer(QWidget):
    """
    Floating pomodoro clock shown at the loading indicator anchor.
    """
    sound_path = Path(__file__).resolve().parents[2] / "resources" / "sounds" / "06-end-duck-round.mp3"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pomodoroTimer")
        self.setFixedSize(QSize(214, 236))
        self.setWindowTitle("pomodoro")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.work_seconds = 25 * 60
        self.rest_seconds = 5 * 60
        self.current_phase = "work"
        self.remaining_seconds = self.work_seconds
        self.total_seconds = self.work_seconds
        self._waiting_for_sound = False
        self._audio_output = None
        self._media_player = self._create_media_player()

        self.phase_label = QLabel("work", self)
        self.phase_label.setObjectName("pomodoroPhaseLabel")
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("25:00", self)
        self.time_label.setObjectName("pomodoroTimeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(34)
        font.setWeight(QFont.Weight.Light)
        self.time_label.setFont(font)

        self.reset_button = QPushButton(self)
        self.reset_button.setObjectName("pomodoroResetButton")
        self.reset_button.setToolTip("Reset pomodoro")
        self.reset_button.setIcon(self.control_icon("reset", QColor(34, 211, 238)))
        self.reset_button.setIconSize(QSize(17, 17))
        self.reset_button.clicked.connect(self.reset)

        self.pause_button = QPushButton(self)
        self.pause_button.setObjectName("pomodoroPauseButton")
        self.pause_button.setToolTip("Pause pomodoro")
        self.pause_button.setIcon(self.control_icon("pause", QColor(34, 211, 238)))
        self.pause_button.setIconSize(QSize(17, 17))
        self.pause_button.clicked.connect(self.toggle_pause)

        self.cancel_button = QPushButton(self)
        self.cancel_button.setObjectName("pomodoroCancelButton")
        self.cancel_button.setToolTip("Cancel pomodoro")
        self.cancel_button.setIcon(self.control_icon("cancel", QColor(203, 213, 225)))
        self.cancel_button.setIconSize(QSize(16, 16))
        self.cancel_button.clicked.connect(self.cancel)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)

        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(180)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.layout_controls()

    def control_icon(self, name: str, color: QColor):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(color)

        if name == "pause":
            painter.drawRoundedRect(7, 5, 3, 14, 1.5, 1.5)
            painter.drawRoundedRect(14, 5, 3, 14, 1.5, 1.5)
        elif name == "play":
            points = [
                QPoint(8, 5),
                QPoint(8, 19),
                QPoint(18, 12),
            ]
            painter.drawPolygon(points)
        elif name == "reset":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(5, 5, 14, 14), 55 * 16, 260 * 16)
            painter.setBrush(color)
            painter.drawPolygon([QPoint(17, 4), QPoint(20, 10), QPoint(13, 9)])
        elif name == "cancel":
            painter.drawLine(7, 7, 17, 17)
            painter.drawLine(17, 7, 7, 17)

        painter.end()
        return QIcon(pixmap)

    def layout_controls(self) -> None:
        self.phase_label.setGeometry(65, 47, 84, 20)
        self.time_label.setGeometry(18, 74, 178, 56)
        self.pause_button.setGeometry(89, 136, 36, 32)
        self.reset_button.setGeometry(70, 199, 34, 24)
        self.cancel_button.setGeometry(110, 199, 34, 24)

    def resizeEvent(self, event) -> None:
        self.layout_controls()
        super().resizeEvent(event)

    def start(self, work_minutes: int, rest_minutes: int, restart: bool = True) -> None:
        self.work_seconds = max(1, int(work_minutes)) * 60
        self.rest_seconds = max(1, int(rest_minutes)) * 60
        if restart or self.remaining_seconds <= 0:
            self.current_phase = "work"
            self.total_seconds = self.work_seconds
            self.remaining_seconds = self.total_seconds
        self.update_labels()
        self.pause_button.setToolTip("Pause pomodoro")
        self.pause_button.setIcon(self.control_icon("pause", QColor(34, 211, 238)))
        self.show()
        self.raise_()
        if restart:
            self.setWindowOpacity(0.0)
            self.opacity_animation.start()
        self.timer.start()

    def stop(self) -> None:
        if self._waiting_for_sound:
            return
        self.timer.stop()
        self.pause_button.setToolTip("Resume pomodoro")
        self.pause_button.setIcon(self.control_icon("play", QColor(34, 211, 238)))
        self.update_labels()

    def reset(self) -> None:
        self.stop_sound()
        self._waiting_for_sound = False
        self.pause_button.setEnabled(True)
        self.current_phase = "work"
        self.total_seconds = self.work_seconds
        self.remaining_seconds = self.total_seconds
        self.pause_button.setToolTip("Pause pomodoro")
        self.pause_button.setIcon(self.control_icon("pause", QColor(34, 211, 238)))
        self.update_labels()
        self.update()
        self.timer.start()

    def toggle_pause(self) -> None:
        if self._waiting_for_sound:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setToolTip("Resume pomodoro")
            self.pause_button.setIcon(self.control_icon("play", QColor(34, 211, 238)))
        else:
            self.timer.start()
            self.pause_button.setToolTip("Pause pomodoro")
            self.pause_button.setIcon(self.control_icon("pause", QColor(34, 211, 238)))

    def cancel(self) -> None:
        self.stop_sound()
        self._waiting_for_sound = False
        self.pause_button.setEnabled(True)
        self.timer.stop()
        self.pause_button.setToolTip("Pause pomodoro")
        self.pause_button.setIcon(self.control_icon("pause", QColor(34, 211, 238)))
        self.hide()

    def tick(self) -> None:
        if self._waiting_for_sound:
            return
        self.remaining_seconds = max(0, self.remaining_seconds - 1)
        if self.remaining_seconds <= 0:
            self.update_labels()
            self.update()
            self.start_phase_transition()
            return
        self.update_labels()
        self.update()

    def start_phase_transition(self) -> None:
        self.timer.stop()
        self._waiting_for_sound = True
        self.pause_button.setEnabled(False)
        self.pause_button.setToolTip("Waiting for sound to finish")
        if not self.play_duck_sound():
            QTimer.singleShot(1000, self.complete_phase_transition)

    def complete_phase_transition(self) -> None:
        if not self._waiting_for_sound:
            return
        self._waiting_for_sound = False
        self.pause_button.setEnabled(True)
        self.pause_button.setToolTip("Pause pomodoro")
        self.pause_button.setIcon(self.control_icon("pause", QColor(34, 211, 238)))
        self.switch_phase()
        self.update_labels()
        self.update()
        self.timer.start()

    def switch_phase(self) -> None:
        if self.current_phase == "work":
            self.current_phase = "rest"
            self.total_seconds = self.rest_seconds
        else:
            self.current_phase = "work"
            self.total_seconds = self.work_seconds
        self.remaining_seconds = self.total_seconds

    def update_labels(self) -> None:
        minutes, seconds = divmod(max(0, self.remaining_seconds), 60)
        self.phase_label.setText("focus" if self.current_phase == "work" else "rest")
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def progress(self) -> float:
        if self.total_seconds <= 0:
            return 0
        return 1 - (self.remaining_seconds / self.total_seconds)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(5, 5, -5, -5)
        center = rect.center()

        gradient = QRadialGradient(float(center.x()), float(center.y()), rect.height() / 1.35)
        gradient.setColorAt(0.0, QColor(20, 184, 166, 55))
        gradient.setColorAt(0.62, QColor(15, 23, 42, 242))
        gradient.setColorAt(1.0, QColor(2, 6, 23, 225))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(34, 211, 238, 180), 1.5))
        painter.drawRoundedRect(rect, 28, 28)

        dial_rect = QRectF(23, 24, 168, 168)
        painter.setBrush(QColor(8, 13, 26, 96))
        painter.setPen(QPen(QColor(125, 211, 252, 48), 1))
        painter.drawEllipse(dial_rect.adjusted(8, 8, -8, -8))

        painter.setPen(QPen(QColor(51, 65, 85, 210), 7))
        painter.drawArc(dial_rect, 90 * 16, -360 * 16)

        color = QColor(34, 211, 238) if self.current_phase == "work" else QColor(52, 211, 153)
        painter.setPen(QPen(color, 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(dial_rect, 90 * 16, int(-360 * self.progress() * 16))

        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        knob_angle = (90 - (360 * self.progress())) * math.pi / 180
        knob_center = dial_rect.center()
        knob_radius = dial_rect.width() / 2
        painter.drawEllipse(
            QPointF(
                knob_center.x() + math.cos(knob_angle) * knob_radius,
                knob_center.y() - math.sin(knob_angle) * knob_radius,
            ),
            8,
            8,
        )
        super().paintEvent(event)

    def _create_media_player(self):
        if QMediaPlayer is None or QAudioOutput is None:
            return None
        if not self.sound_path.exists():
            return None
        self._audio_output = QAudioOutput(self)
        self._audio_output.setVolume(0.85)
        player = QMediaPlayer(self)
        player.setAudioOutput(self._audio_output)
        player.setSource(QUrl.fromLocalFile(str(self.sound_path)))
        player.mediaStatusChanged.connect(self.on_media_status_changed)
        player.errorOccurred.connect(self.on_media_error)
        return player

    def play_duck_sound(self) -> bool:
        if self._media_player is not None:
            self._media_player.stop()
            self._media_player.setPosition(0)
            self._media_player.play()
            return True
        QApplication.beep()
        return False

    def stop_sound(self) -> None:
        if self._media_player is not None:
            self._media_player.stop()

    def on_media_status_changed(self, status) -> None:
        if (
            self._waiting_for_sound
            and QMediaPlayer is not None
            and status == QMediaPlayer.MediaStatus.EndOfMedia
        ):
            self.complete_phase_transition()

    def on_media_error(self, *args) -> None:
        if self._waiting_for_sound:
            QTimer.singleShot(1000, self.complete_phase_transition)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()
        else:
            super().keyPressEvent(event)
