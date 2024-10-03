import sys
import logging
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QLabel, QFileDialog,QHBoxLayout, QProgressBar, QFormLayout, QTextEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from utils import download_video_or_playlist

# Custom logging handler to emit logs to QTextEdit in the GUI
class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())  # Scroll to bottom
        QApplication.processEvents()  # Ensure logs update in real-time


# Download threads for processing videos
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
            self.finished_signal.emit("Download success!")
        except Exception as e:
            self.finished_signal.emit(f"Error: {e}")


class DownloadApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(1000, 500, 900, 600)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.myproduct.subproduct.version")

        self.initUI()
        self.setup_logging()


    def initUI(self):
         # Set dark theme
        dark_theme = """
            QWidget {
                background-color: #2E2E2E;
                color: #F0F0F0;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: #F0F0F0;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton#BrowseButton {
                padding: 5px;
                border-radius: 10px;
            }
            QLabel {
                color: #F0F0F0;
            }
            QLineEdit {
                color: #F0F0F0;
                background-color: #1c1c1c;
                border: 2px solid #1c1c1c;
                padding: 5px;
            }
            QProgressBar {
                background-color: #4A4A4A;
                border: 1px solid #F0F0F0;
                color: #F0F0F0;
            }
            QProgressBar::chunk {
                background-color: #1cb81c;
            }
        """
        self.setStyleSheet(dark_theme)
        # Create widgets
        self.url_label = QLabel("YouTube URL:", self)
        self.url_input = QLineEdit(self)

        self.output_label = QLabel("Output Directory:", self)
        self.output_input = QLineEdit(self)
        
        # Browse button
        self.browse_button = QPushButton("Browse...", self)
        self.browse_button.setFixedWidth(80)
        self.browse_button.clicked.connect(self.browse_directory)

        self.browse_button.setObjectName("BrowseButton") #For CSS styling

        # Start download button
        self.start_button = QPushButton("Start Download", self)
        self.start_button.clicked.connect(self.start_download)

        self.start_button.setObjectName("DownloadButton") #For CSS styling

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel("", self)

        # Text area for logging
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)


        # Horizontal layout for output directory and Browse button
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(self.browse_button)

        # Form layout for labels and inputs
        form_layout = QFormLayout()
        form_layout.addRow(self.url_label, self.url_input)
        form_layout.addRow(output_layout)  # Add horizontal layout for output + button
        form_layout.setContentsMargins(20, 20, 20, 0)  # Adjust margins as needed

        # Vertical layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)  # Add the form layout
        layout.addWidget(self.start_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_text)  # Add log text area to layout

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def setup_logging(self):
        """
        Set up logging to redirect to the QTextEdit in the GUI.
        """
        log_handler = QTextEditLogger(self.log_text)
        log_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)
        
        self.log_text.setFont(QFont('Helvetica', 9))  # Change font to Arial for testing

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
        self.status_label.setText("Extracting info...")
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
    app.setWindowIcon(QIcon("icon.ico"))  # Set the taskbar icon here
    window = DownloadApp()
    window.show()
    sys.exit(app.exec_())
