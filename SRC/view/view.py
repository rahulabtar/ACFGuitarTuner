# needle_dial_tuner.py
import sys
import itertools
from random import random
import colorsys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QDialog, QComboBox, QSpinBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor


# -------------------------
# Model
# -------------------------
class DummyDialModel:
    """Simulates the dial model"""
    def __init__(self):
        self._note = "A"
        self._cents = 0.0
        self._active = True

    def update(self, note, cents, active=True):
        self._note = note
        self._cents = cents
        self._active = active

    def get_note(self):
        return self._note

    def get_cents(self):
        return self._cents

    def get_value(self):
        return self._cents

    def is_active(self):
        return self._active

# -------------------------
# Needle Dial Widget
# -------------------------
class NeedleDial(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0  # cents: -50 to +50
        self.isActive = False
        self.setMinimumSize(200, 200)

    def set_value(self, val):
        self.value = max(min(val, 50), -50)  # clamp
        self.update()
    
    def set_active(self, active: bool):
        self.isActive = active
        if not active:
            self.value = 0   # snap needle to center
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = min(w, h) // 2 - 10
        cx, cy = w // 2, h // 2

        if not self.isActive:
            painter.setPen(QPen(QColor("#7f8c8d"), 20))  # grey arc
            painter.drawArc(
                cx - radius, cy - radius,
                radius * 2, radius * 2,
                180 * 16, -180 * 16
            )

            # Grey centered needle
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(0)  # center
            painter.setPen(QPen(QColor("#bdc3c7"), 4))
            #painter.drawLine(0, 0, radius - 20, 0)
            painter.restore()
            return


        # HSV color mapping based on cents
        abs_cents = abs(self.value)
        if abs_cents <= 10:
            hue = 120 - (abs_cents / 10) * 60  # Green → Yellow
            sat = 1.0
            val = 1.0
        else:
            hue = max(0, 60 - ((abs_cents - 10) / 40) * 60)  # Yellow → Red
            sat = 1.0
            val = max(0.5, 1.0 - ((abs_cents - 10) / 40) * 0.5)

        r, g, b = colorsys.hsv_to_rgb(hue / 360, sat, val)
        color = QColor(int(r*255), int(g*255), int(b*255))

        # Draw colored outer circle
        # Draw colored semicircle arc (9 o'clock → 3 o'clock)
        painter.setPen(QPen(color, 20))
        painter.drawArc(
            cx - radius, cy - radius,
            radius * 2, radius * 2,
            180 * 16,   # start at 9 o'clock
            -180 * 16   # sweep to 3 o'clock
)

        # Draw needle
        painter.setPen(QPen(Qt.red, 4))
        angle = (self.value + 50) * 180 / 100  - 90 # map -50→+50 to 0→180 degrees
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(angle - 90)
        painter.drawLine(0, 0, radius - 20, 0)
        painter.restore()

# -------------------------
# Dial Panel
# -------------------------
class DialWidget(QWidget):
    def __init__(self, dial_model):
        super().__init__()
        self.dial_model = dial_model

        self.isActive = False 

        # Note label
        self.note_label = QLabel("--")
        self.note_label.setAlignment(Qt.AlignCenter)
        self.note_label.setStyleSheet("font-size: 48px;")

        # Cents label
        self.cents_label = QLabel("--")
        self.cents_label.setAlignment(Qt.AlignCenter)
        self.cents_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        # Needle dial
        self.needle_dial = NeedleDial()

        layout = QVBoxLayout()
        layout.addWidget(self.note_label)
        layout.addWidget(self.cents_label)
        layout.addWidget(self.needle_dial)
        self.setLayout(layout)

    def display(self):
        active = self.dial_model.is_active()
        self.needle_dial.set_active(active)

        if not active:
            self.note_label.setText("--")
            self.cents_label.setText("--")
            return

        cents = int(self.dial_model.get_cents())
        note = self.dial_model.get_note()

        self.note_label.setText(note)
        self.cents_label.setText(f"{cents:+d}¢")
        self.needle_dial.set_value(cents)

# -------------------------
# Settings Dialog
# -------------------------
class SettingsDialog(QDialog):
    settings_applied = pyqtSignal(dict)

    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        # Input device
        self.device_box = QComboBox()
        for dev_id, name, channels in devices:
            self.device_box.addItem(name, dev_id)
        layout.addWidget(QLabel("Input Device"))
        layout.addWidget(self.device_box)

        # Channel
        self.channel_box = QComboBox()
        for ch in range(2):
            self.channel_box.addItem(f"Ch {ch}", ch)
        layout.addWidget(QLabel("Channel"))
        layout.addWidget(self.channel_box)

        # Buffer size
        self.buffer_spin = QSpinBox()
        self.buffer_spin.setRange(64, 16384)
        self.buffer_spin.setValue(2048)
        layout.addWidget(QLabel("Buffer Size"))
        layout.addWidget(self.buffer_spin)

        # Block size
        self.block_spin = QSpinBox()
        self.block_spin.setRange(32, 8192)
        self.block_spin.setValue(512)
        layout.addWidget(QLabel("Block Size"))
        layout.addWidget(self.block_spin)

        # Pitch detection method
        self.method_box = QComboBox()
        self.method_box.addItems(["ACF", "YIN"])
        layout.addWidget(QLabel("Pitch Detection Method"))
        layout.addWidget(self.method_box)

        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)

        self.setLayout(layout)

    def apply_settings(self):
        settings = {
            "device_id": self.device_box.currentData(),
            "channel": self.channel_box.currentData(),
            "buffer_size": self.buffer_spin.value(),
            "block_size": self.block_spin.value(),
            "method": self.method_box.currentText()
        }
        self.settings_applied.emit(settings)
        self.accept()


# -------------------------
# Main Window
# -------------------------
class MainWindow(QWidget):
    def __init__(self, dial_model, devices):
        super().__init__()
        self.dial_panel = DialWidget(dial_model)
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(lambda: self.open_settings(devices))

        layout = QVBoxLayout()
        layout.addWidget(self.dial_panel)
        layout.addWidget(self.settings_btn)
        self.setLayout(layout)

    def open_settings(self, devices):
        dialog = SettingsDialog(devices, self)
        dialog.settings_applied.connect(self.apply_new_settings)
        dialog.exec_()

    def apply_new_settings(self, settings):
        print("Settings applied:", settings)
        # Connect to Controller to reconfigure AudioIn / Pitcher


# -------------------------
# Test / main
# -------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    dial_model = DummyDialModel()
    devices = [(0, "Mic 1", 2), (1, "Mic 2", 2)]

    window = MainWindow(dial_model, devices)
    window.setWindowTitle("YAGT - ACF Based Tuner")
    window.resize(400, 450)
    window.show()

    # Dummy data updates
    notes = itertools.cycle(["E", "A", "D", "G", "B", "E"])
    cents_sweep = itertools.cycle(range(-50, 51, 2))
    current_note = next(notes)

    def update_dummy_data():
        global current_note
        active = random() > 0.1
        if not active:
            dial_model.update("--", 0, active=False)
        else:
            cents = next(cents_sweep)
            if abs(cents) <= 2:
                current_note = next(notes)
            dial_model.update(current_note, cents, active=True)
        window.dial_panel.display()

    timer = QTimer()
    timer.timeout.connect(update_dummy_data)
    timer.start(40)

    sys.exit(app.exec_())
