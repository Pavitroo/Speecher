import sys
import sounddevice as sd
import numpy as np
import wave
import os
import threading
from gtts import gTTS
from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QWidget, QPushButton, 
                             QTextEdit, QLabel, QComboBox, QHBoxLayout, 
                             QProgressBar, QSlider, QFileDialog)
from PyQt6.QtCore import pyqtSignal, QObject, Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

class Recorder(QObject):
    recording_complete = pyqtSignal()
    progress_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.recording = False
        self.duration = 5  # Default duration

    def record(self):
        fs = 44100  # Sample rate
        self.recording = True

        print("Recording...")
        recording = sd.rec(int(self.duration * fs), samplerate=fs, channels=2)
        
        for i in range(self.duration):
            if not self.recording:
                break
            self.progress_updated.emit((i + 1) * 100 // self.duration)
            sd.sleep(1000)
        
        sd.stop()
        print("Recording complete.")

        if self.recording:
            with wave.open("user_voice.wav", 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(recording.tobytes())

        self.recording = False
        self.recording_complete.emit()

    def stop(self):
        self.recording = False

class VoiceCloneApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Modern Voice Clone App")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

        self.recorder = Recorder()
        self.recorder.recording_complete.connect(self.on_recording_complete)
        self.recorder.progress_updated.connect(self.update_progress)

        self.recording_thread = None

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #3498DB;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
            QTextEdit, QComboBox {
                background-color: #34495E;
                border: 1px solid #7F8C8D;
                border-radius: 5px;
                padding: 5px;
                color: #ECF0F1;
            }
            QLabel {
                font-size: 18px;
            }
            QProgressBar {
                border: 2px solid #7F8C8D;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #27AE60;
                width: 10px;
                margin: 0.5px;
            }
        """)

        layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text to convert to speech...")
        layout.addWidget(self.text_input)

        voice_layout = QHBoxLayout()
        self.voice_label = QLabel("Select Voice:")
        self.voice_selection = QComboBox()
        self.voice_selection.addItems(["hi", "en", "fr", "de", "es", "it", "ja", "ko"])
        voice_layout.addWidget(self.voice_label)
        voice_layout.addWidget(self.voice_selection)
        layout.addLayout(voice_layout)

        self.duration_label = QLabel("Recording Duration: 5 seconds")
        layout.addWidget(self.duration_label)

        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setMinimum(1)
        self.duration_slider.setMaximum(30)
        self.duration_slider.setValue(5)
        self.duration_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.duration_slider.setTickInterval(5)
        self.duration_slider.valueChanged.connect(self.update_duration)
        layout.addWidget(self.duration_slider)

        button_layout = QHBoxLayout()
        self.record_button = QPushButton("Record Your Voice")
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)

        self.convert_button = QPushButton("Convert Text to Speech")
        self.convert_button.clicked.connect(self.convert_text_to_speech)
        button_layout.addWidget(self.convert_button)

        self.save_button = QPushButton("Save Audio")
        self.save_button.clicked.connect(self.save_audio)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def update_duration(self, value):
        self.duration_label.setText(f"Recording Duration: {value} seconds")
        self.recorder.duration = value

    def toggle_recording(self):
        if not self.recorder.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.record_button.setText("Stop Recording")
        self.status_label.setText("Recording...")
        self.progress_bar.setValue(0)
        self.recording_thread = threading.Thread(target=self.recorder.record)
        self.recording_thread.start()

    def stop_recording(self):
        self.recorder.stop()
        self.record_button.setText("Record Your Voice")
        self.status_label.setText("Recording stopped")

    def on_recording_complete(self):
        self.record_button.setText("Record Your Voice")
        self.status_label.setText("Recording saved")
        self.progress_bar.setValue(100)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def convert_text_to_speech(self):
        text = self.text_input.toPlainText()
        lang_code = self.voice_selection.currentText()
        
        self.status_label.setText("Converting text to speech...")
        self.progress_bar.setValue(0)

        def convert():
            tts = gTTS(text=text, lang=lang_code)
            tts.save("output.mp3")
            self.status_label.setText("Conversion complete")
            self.progress_bar.setValue(100)
            os.system("start output.mp3")

        threading.Thread(target=convert).start()

    def save_audio(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Audio File", "", "MP3 Files (*.mp3)")
        if file_path:
            if os.path.exists("output.mp3"):
                os.rename("output.mp3", file_path)
                self.status_label.setText(f"Audio saved to {file_path}")
            else:
                self.status_label.setText("No audio to save. Convert text to speech first.")

    def closeEvent(self, event):
        if self.recording_thread and self.recording_thread.is_alive():
            self.recorder.stop()
            self.recording_thread.join()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceCloneApp()
    window.show()
    sys.exit(app.exec())