import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QListWidget, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from video_concatenator import main as concatenator_main

class ProcessThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, input_files, timestamp_files, output_file, output_timestamp_file):
        QThread.__init__(self)
        self.input_files = input_files
        self.timestamp_files = timestamp_files
        self.output_file = output_file
        self.output_timestamp_file = output_timestamp_file

    def run(self):
        try:
            # Convert "[No Timestamp File]" to None for compatibility with the logic script
            adjusted_timestamp_files = [None if t == "[No Timestamp File]" else t for t in self.timestamp_files]
            concatenator_main(self.input_files, adjusted_timestamp_files, self.output_file, self.output_timestamp_file)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class VideoConcatenatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Video files column
        videoLayout = QVBoxLayout()
        videoLayout.addWidget(QLabel('Video Files'))
        
        videoButtonLayout = QHBoxLayout()
        self.addVideoButton = QPushButton('Add Video')
        self.addVideoButton.clicked.connect(self.addInputFile)
        videoButtonLayout.addWidget(self.addVideoButton)

        self.removeVideoButton = QPushButton('Remove Selected')
        self.removeVideoButton.clicked.connect(self.removeSelectedFile)
        videoButtonLayout.addWidget(self.removeVideoButton)

        self.moveVideoUpButton = QPushButton('Move Up')
        self.moveVideoUpButton.clicked.connect(self.moveVideoUp)
        videoButtonLayout.addWidget(self.moveVideoUpButton)

        self.moveVideoDownButton = QPushButton('Move Down')
        self.moveVideoDownButton.clicked.connect(self.moveVideoDown)
        videoButtonLayout.addWidget(self.moveVideoDownButton)

        videoLayout.addLayout(videoButtonLayout)

        self.videoListWidget = QListWidget()
        videoLayout.addWidget(self.videoListWidget)

        layout.addLayout(videoLayout)

        # Timestamp files column
        timestampLayout = QVBoxLayout()
        timestampLayout.addWidget(QLabel('Timestamp Files'))
        
        timestampButtonLayout = QHBoxLayout()
        self.addTimestampButton = QPushButton('Add Timestamp')
        self.addTimestampButton.clicked.connect(self.addTimestampFile)
        timestampButtonLayout.addWidget(self.addTimestampButton)

        self.removeTimestampButton = QPushButton('Remove Selected')
        self.removeTimestampButton.clicked.connect(self.removeSelectedTimestamp)
        timestampButtonLayout.addWidget(self.removeTimestampButton)

        self.moveTimestampUpButton = QPushButton('Move Up')
        self.moveTimestampUpButton.clicked.connect(self.moveTimestampUp)
        timestampButtonLayout.addWidget(self.moveTimestampUpButton)

        self.moveTimestampDownButton = QPushButton('Move Down')
        self.moveTimestampDownButton.clicked.connect(self.moveTimestampDown)
        timestampButtonLayout.addWidget(self.moveTimestampDownButton)

        timestampLayout.addLayout(timestampButtonLayout)

        self.addPlaceholderButton = QPushButton('Add Placeholder')
        self.addPlaceholderButton.clicked.connect(self.addTimestampPlaceholder)
        timestampLayout.addWidget(self.addPlaceholderButton)

        self.timestampListWidget = QListWidget()
        timestampLayout.addWidget(self.timestampListWidget)

        layout.addLayout(timestampLayout)

        # Output selection
        outputLayout = QVBoxLayout()
        
        self.outputFileButton = QPushButton('Select Output Video File')
        self.outputFileButton.clicked.connect(self.selectOutputFile)
        self.outputFileLabel = QLabel('No video file selected')
        outputLayout.addWidget(self.outputFileButton)
        outputLayout.addWidget(self.outputFileLabel)

        self.outputTimestampButton = QPushButton('Select Output Timestamp File')
        self.outputTimestampButton.clicked.connect(self.selectOutputTimestampFile)
        self.outputTimestampLabel = QLabel('No timestamp file selected')
        outputLayout.addWidget(self.outputTimestampButton)
        outputLayout.addWidget(self.outputTimestampLabel)

        self.processButton = QPushButton('Concatenate Videos and Merge Timestamps')
        self.processButton.clicked.connect(self.processVideos)
        outputLayout.addWidget(self.processButton)

        self.statusLabel = QLabel('Ready')
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.statusLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outputLayout.addWidget(self.statusLabel)

        layout.addLayout(outputLayout)

        self.setLayout(layout)
        self.setWindowTitle('Video Concatenator with Timestamp Merger')
        self.setMinimumSize(800, 600)
        self.setMaximumWidth(1200)
        self.show()

    def addInputFile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Input Video File", "", "MP4 Files (*.mp4)")
        if file:
            self.videoListWidget.addItem(file)

    def addTimestampFile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Timestamp File", "", "Text Files (*.txt)")
        if file:
            self.timestampListWidget.addItem(file)

    def addTimestampPlaceholder(self):
        self.timestampListWidget.addItem("[No Timestamp File]")

    def removeSelectedFile(self):
        for item in self.videoListWidget.selectedItems():
            self.videoListWidget.takeItem(self.videoListWidget.row(item))

    def removeSelectedTimestamp(self):
        for item in self.timestampListWidget.selectedItems():
            self.timestampListWidget.takeItem(self.timestampListWidget.row(item))

    def moveVideoUp(self):
        currentRow = self.videoListWidget.currentRow()
        if currentRow > 0:
            item = self.videoListWidget.takeItem(currentRow)
            self.videoListWidget.insertItem(currentRow - 1, item)
            self.videoListWidget.setCurrentItem(item)

    def moveVideoDown(self):
        currentRow = self.videoListWidget.currentRow()
        if currentRow < self.videoListWidget.count() - 1:
            item = self.videoListWidget.takeItem(currentRow)
            self.videoListWidget.insertItem(currentRow + 1, item)
            self.videoListWidget.setCurrentItem(item)

    def moveTimestampUp(self):
        currentRow = self.timestampListWidget.currentRow()
        if currentRow > 0:
            item = self.timestampListWidget.takeItem(currentRow)
            self.timestampListWidget.insertItem(currentRow - 1, item)
            self.timestampListWidget.setCurrentItem(item)

    def moveTimestampDown(self):
        currentRow = self.timestampListWidget.currentRow()
        if currentRow < self.timestampListWidget.count() - 1:
            item = self.timestampListWidget.takeItem(currentRow)
            self.timestampListWidget.insertItem(currentRow + 1, item)
            self.timestampListWidget.setCurrentItem(item)

    def selectOutputFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output Video File", "", "MP4 Files (*.mp4)")
        if filename:
            self.outputFileLabel.setText(filename)
            timestamp_filename = filename.rsplit('.', 1)[0] + '_timestamps.txt'
            self.outputTimestampLabel.setText(timestamp_filename)

    def selectOutputTimestampFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output Timestamp File", "", "Text Files (*.txt)")
        if filename:
            self.outputTimestampLabel.setText(filename)

    def processVideos(self):
        input_files = [self.videoListWidget.item(i).text() for i in range(self.videoListWidget.count())]
        timestamp_files = [self.timestampListWidget.item(i).text() for i in range(self.timestampListWidget.count())]
        output_file = self.outputFileLabel.text()
        output_timestamp_file = self.outputTimestampLabel.text()

        if not input_files:
            QMessageBox.warning(self, "Error", "Please select input files.")
            return

        if output_file == 'No video file selected':
            QMessageBox.warning(self, "Error", "Please select an output video file.")
            return

        if timestamp_files and output_timestamp_file == 'No timestamp file selected':
            QMessageBox.warning(self, "Error", "Please select an output timestamp file or remove all timestamp inputs.")
            return

        self.processButton.setEnabled(False)
        self.statusLabel.setText("Processing...")

        self.thread = ProcessThread(input_files, timestamp_files, output_file, output_timestamp_file)
        self.thread.finished.connect(self.onProcessingFinished)
        self.thread.error.connect(self.onProcessingError)
        self.thread.start()

    def onProcessingFinished(self):
        self.statusLabel.setText("Processing completed successfully!")
        self.processButton.setEnabled(True)

    def onProcessingError(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.statusLabel.setText("An error occurred.")
        self.processButton.setEnabled(True)

    def resizeEvent(self, event):
        self.statusLabel.setFixedWidth(self.width() - 40)
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoConcatenatorGUI()
    sys.exit(app.exec_())