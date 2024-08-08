import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QListWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import subprocess
from pathlib import Path

class ProcessThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, input_files, output_file):
        QThread.__init__(self)
        self.input_files = input_files
        self.output_file = output_file

    def run(self):
        try:
            self.progress.emit("Checking FFmpeg installation...")
            if not self.check_ffmpeg():
                self.error.emit("FFmpeg is not installed or not in the system PATH.")
                return

            self.progress.emit("Validating input files...")
            valid_files = self.validate_input_files(self.input_files)
            if not valid_files:
                self.error.emit("No valid input files found.")
                return

            self.progress.emit("Concatenating videos...")
            self.concatenate_videos(valid_files, self.output_file)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def validate_input_files(self, file_paths):
        valid_files = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                self.progress.emit(f"Error: File not found: {file_path}")
            elif not path.is_file():
                self.progress.emit(f"Error: Not a file: {file_path}")
            elif path.suffix.lower() != '.mp4':
                self.progress.emit(f"Error: Not an MP4 file: {file_path}")
            else:
                valid_files.append(str(path.resolve()))
        return valid_files

    def get_video_info(self, file_path):
        try:
            result = subprocess.run([
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-count_packets",
                "-show_entries", "stream=width,height,r_frame_rate,codec_name",
                "-of", "csv=p=0",
                file_path
            ], capture_output=True, text=True, check=True)
            
            output = result.stdout.strip().split(',')
            
            if len(output) != 4:
                self.progress.emit(f"Unexpected ffprobe output format: {output}")
                return None

            info = {
                'codec': output[0],
                'width': int(output[1]),
                'height': int(output[2]),
                'frame_rate': eval(output[3])
            }

            return info
        except subprocess.CalledProcessError as e:
            self.progress.emit(f"Error running ffprobe: {e}")
            return None
        except ValueError as e:
            self.progress.emit(f"Error parsing ffprobe output: {e}")
            self.progress.emit(f"ffprobe output: {result.stdout}")
            return None

    def concatenate_videos(self, input_files, output_file):
        first_video_info = self.get_video_info(input_files[0])
        if not first_video_info:
            self.error.emit("Failed to get video info for the first file. Aborting.")
            return

        filter_complex = []
        inputs = []
        
        for i, file in enumerate(input_files):
            inputs.extend(['-i', file])
            filter_complex.append(f'[{i}:v]scale={first_video_info["width"]}:{first_video_info["height"]}:force_original_aspect_ratio=decrease,pad={first_video_info["width"]}:{first_video_info["height"]}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={first_video_info["frame_rate"]}[v{i}];')
            filter_complex.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}];')

        for i in range(len(input_files)):
            filter_complex.append(f'[v{i}][a{i}]')
        
        filter_complex.append(f'concat=n={len(input_files)}:v=1:a=1[outv][outa]')
        
        try:
            cmd = [
                "ffmpeg",
                *inputs,
                '-filter_complex', ''.join(filter_complex),
                '-map', '[outv]',
                '-map', '[outa]',
                '-c:v', first_video_info['codec'],
                '-c:a', 'aac',
                output_file
            ]
            self.progress.emit("Running FFmpeg command...")
            subprocess.run(cmd, check=True)
            self.progress.emit(f"Concatenation complete. Output saved to {output_file}")
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Error during concatenation: {e}")
class VideoConcatenatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input files selection
        inputLayout = QHBoxLayout()
        self.addFileButton = QPushButton('Add File')
        self.addFileButton.clicked.connect(self.addInputFile)
        inputLayout.addWidget(self.addFileButton)

        self.removeFileButton = QPushButton('Remove Selected')
        self.removeFileButton.clicked.connect(self.removeSelectedFile)
        inputLayout.addWidget(self.removeFileButton)

        self.moveUpButton = QPushButton('Move Up')
        self.moveUpButton.clicked.connect(self.moveFileUp)
        inputLayout.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton('Move Down')
        self.moveDownButton.clicked.connect(self.moveFileDown)
        inputLayout.addWidget(self.moveDownButton)

        layout.addLayout(inputLayout)

        # List of selected files
        self.fileListWidget = QListWidget()
        layout.addWidget(self.fileListWidget)

        # Output file selection
        self.outputFileButton = QPushButton('Select Output File')
        self.outputFileButton.clicked.connect(self.selectOutputFile)
        self.outputFileLabel = QLabel('No file selected')
        layout.addWidget(self.outputFileButton)
        layout.addWidget(self.outputFileLabel)

        # Process button
        self.processButton = QPushButton('Concatenate Videos')
        self.processButton.clicked.connect(self.processVideos)
        layout.addWidget(self.processButton)

        # Status label
        self.statusLabel = QLabel('Ready')
        layout.addWidget(self.statusLabel)

        self.setLayout(layout)
        self.setWindowTitle('Video Concatenator')
        self.show()

    def addInputFile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Input Video File", "", "MP4 Files (*.mp4)")
        if file:
            self.fileListWidget.addItem(file)

    def removeSelectedFile(self):
        for item in self.fileListWidget.selectedItems():
            self.fileListWidget.takeItem(self.fileListWidget.row(item))

    def moveFileUp(self):
        currentRow = self.fileListWidget.currentRow()
        if currentRow > 0:
            item = self.fileListWidget.takeItem(currentRow)
            self.fileListWidget.insertItem(currentRow - 1, item)
            self.fileListWidget.setCurrentItem(item)

    def moveFileDown(self):
        currentRow = self.fileListWidget.currentRow()
        if currentRow < self.fileListWidget.count() - 1:
            item = self.fileListWidget.takeItem(currentRow)
            self.fileListWidget.insertItem(currentRow + 1, item)
            self.fileListWidget.setCurrentItem(item)

    def selectOutputFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output Video File", "", "MP4 Files (*.mp4)")
        if filename:
            self.outputFileLabel.setText(filename)

    def processVideos(self):
        input_files = [self.fileListWidget.item(i).text() for i in range(self.fileListWidget.count())]
        output_file = self.outputFileLabel.text()

        if not input_files:
            QMessageBox.warning(self, "Error", "Please select input files.")
            return

        if output_file == 'No file selected':
            QMessageBox.warning(self, "Error", "Please select an output file.")
            return

        # Disable the process button
        self.processButton.setEnabled(False)
        self.statusLabel.setText("Processing...")

        # Create and start the processing thread
        self.thread = ProcessThread(input_files, output_file)
        self.thread.finished.connect(self.onProcessingFinished)
        self.thread.error.connect(self.onProcessingError)
        self.thread.progress.connect(self.updateStatus)
        self.thread.start()

    def onProcessingFinished(self):
        self.statusLabel.setText("Processing completed successfully!")
        self.processButton.setEnabled(True)

    def onProcessingError(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.statusLabel.setText("An error occurred.")
        self.processButton.setEnabled(True)

    def updateStatus(self, message):
        self.statusLabel.setText(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoConcatenatorGUI()
    sys.exit(app.exec_())