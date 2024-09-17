import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QLabel, QFileDialog, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from utils import download_video_or_playlist

class DownloadThread(QThread):
    progress_signal = pyqtSignal(float)
    finished_signal = pyqtSignal(str)
    
    def __init__(self, url, output_directory):
        super().__init__()
        self.url = url
        self.output_directory = output_directory

    def run(self):
        def progress_callback(progress, video_title=None):
            self.progress_signal.emit(progress)
            if video_title:
                self.finished_signal.emit(video_title)  # Emit video title for playlists
            else:
                self.finished_signal.emit(f"Downloading video... {int(progress)}%")

        try:
            download_video_or_playlist(self.url, self.output_directory, progress_callback)
            self.finished_signal.emit("All videos downloaded successfully!")
        except Exception as e:
            self.finished_signal.emit(f"Error: {e}")


class DownloadApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(1000, 500, 600, 400)

        self.initUI()

    def initUI(self):
        # Create widgets
        self.url_label = QLabel("YouTube URL:", self)
        self.url_input = QLineEdit(self)

        self.output_label = QLabel("Output Directory:", self)
        self.output_input = QLineEdit(self)
        self.browse_button = QPushButton("Browse...", self)
        self.browse_button.clicked.connect(self.browse_directory)

        self.start_button = QPushButton("Start Download", self)
        self.start_button.clicked.connect(self.start_download)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("", self)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.output_input.setText(directory)

    def start_download(self):
        url = self.url_input.text()
        output_directory = self.output_input.text()

        if not url or not output_directory:
            self.status_label.setText("Please enter both URL and output directory.")
            return

        self.thread = DownloadThread(url, output_directory)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.show_message)
        self.thread.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(int(progress))

        if int(progress) == 100:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
        else:
            self.progress_bar.setStyleSheet("")  # Reset to default style

    def show_message(self, message):
        self.status_label.setText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadApp()
    window.show()
    sys.exit(app.exec_())
