import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QListWidget, QProgressBar, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ProcessThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_files, timestamp_files, settings):
        QThread.__init__(self)
        self.input_files = input_files
        self.timestamp_files = timestamp_files
        self.settings = settings

    def run(self):
        total_files = len(self.input_files)
        for i, (input_file, timestamp_file) in enumerate(zip(self.input_files, self.timestamp_files)):
            try:
                base, ext = os.path.splitext(input_file)
                output_file = f"{base}_no_silence{ext}"
                output_timestamp_file = f"{base}_no_silence_timestamps.txt" if timestamp_file else None

                command = [
                    'python', 'silence_remover.py',
                    input_file,
                    '-o', output_file,
                    '-d', str(self.settings['db_threshold']),
                    '-b', str(self.settings['buffer_duration']),
                    '-c', str(self.settings['chunk_duration']),
                    '-m', str(self.settings['min_silence_factor'])
                ]

                if timestamp_file:
                    command.extend(['-t', timestamp_file])
                if output_timestamp_file:
                    command.extend(['--output_timestamps', output_timestamp_file])

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
                for line in iter(process.stdout.readline, ''):
                    self.progress.emit(int((i / total_files) * 100), f"Processing file {i+1}/{total_files}: {line.strip()}")
                process.stdout.close()
                return_code = process.wait()
                if return_code != 0:
                    self.error.emit(f"Error processing file {input_file}")
                    return

            except Exception as e:
                self.error.emit(str(e))
                return

        self.finished.emit()

class BatchSilenceRemoverGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input files
        inputLayout = QHBoxLayout()
        
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

        inputLayout.addLayout(videoLayout)

        # Add a checkbox for using timestamp files
        self.useTimestampsCheckbox = QCheckBox("Use Timestamp Files")
        self.useTimestampsCheckbox.setChecked(True)
        self.useTimestampsCheckbox.stateChanged.connect(self.toggleTimestampWidgets)
        layout.addWidget(self.useTimestampsCheckbox)

        # Timestamp files column
        self.timestampLayout = QVBoxLayout()
        self.timestampLayout.addWidget(QLabel('Timestamp Files'))
        
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

        #timestampLayout.addLayout(timestampButtonLayout)
        self.timestampLayout.addLayout(timestampButtonLayout)

        self.addPlaceholderButton = QPushButton('Add Placeholder')
        self.addPlaceholderButton.clicked.connect(self.addTimestampPlaceholder)
        #timestampLayout.addWidget(self.addPlaceholderButton)
        self.timestampLayout.addWidget(self.addPlaceholderButton)

        self.timestampListWidget = QListWidget()
        #timestampLayout.addWidget(self.timestampListWidget)
        self.timestampLayout.addWidget(self.timestampListWidget)
        
        #inputLayout.addLayout(timestampLayout)
        inputLayout.addLayout(self.timestampLayout)

        layout.addLayout(inputLayout)

        # Settings
        settingsGroup = QGroupBox("Settings")
        settingsLayout = QFormLayout()

        self.dbThreshold = QDoubleSpinBox()
        self.dbThreshold.setRange(-100, 0)
        self.dbThreshold.setValue(-45)
        self.dbThreshold.setDecimals(1)
        settingsLayout.addRow('Decibel Threshold (dB):', self.dbThreshold)

        self.bufferDuration = QDoubleSpinBox()
        self.bufferDuration.setRange(0, 10)
        self.bufferDuration.setSingleStep(0.1)
        self.bufferDuration.setValue(0.2)
        settingsLayout.addRow('Buffer Duration (s):', self.bufferDuration)

        self.chunkDuration = QSpinBox()
        self.chunkDuration.setRange(1, 3600)
        self.chunkDuration.setValue(150)
        settingsLayout.addRow('Chunk Duration (s):', self.chunkDuration)

        self.minSilenceFactor = QDoubleSpinBox()
        self.minSilenceFactor.setRange(0, 10)
        self.minSilenceFactor.setSingleStep(0.1)
        self.minSilenceFactor.setValue(0.6)
        settingsLayout.addRow('Min Silence Length (s):', self.minSilenceFactor)

        settingsGroup.setLayout(settingsLayout)
        layout.addWidget(settingsGroup)

        # Process button
        self.processButton = QPushButton('Process Videos')
        self.processButton.clicked.connect(self.processVideos)
        layout.addWidget(self.processButton)

        # Progress bar
        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

        # Status label
        self.statusLabel = QLabel('Ready')
        layout.addWidget(self.statusLabel)

        self.setLayout(layout)
        self.setWindowTitle('Batch Silence Remover')
        self.setMinimumSize(800, 600)
        self.show()

    def addInputFile(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Input Video Files", "", "MP4 Files (*.mp4)")
        for file in files:
            self.videoListWidget.addItem(file)

    def addTimestampFile(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Timestamp Files", "", "Text Files (*.txt)")
        for file in files:
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

    def toggleTimestampWidgets(self, state):
        widgets = [self.addTimestampButton, self.removeTimestampButton, 
                   self.moveTimestampUpButton, self.moveTimestampDownButton, 
                   self.addPlaceholderButton, self.timestampListWidget]
        for widget in widgets:
            widget.setEnabled(state == Qt.Checked)
        self.timestampLayout.setEnabled(state == Qt.Checked)

    def processVideos(self):
        input_files = [self.videoListWidget.item(i).text() for i in range(self.videoListWidget.count())]
        #timestamp_files = [self.timestampListWidget.item(i).text() for i in range(self.timestampListWidget.count())]
        
        if not input_files:
            self.statusLabel.setText("Error: No input files selected.")
            return

        #if len(input_files) != len(timestamp_files):
        #    self.statusLabel.setText("Error: Number of input files and timestamp files/placeholders must match.")
        #    return
        use_timestamps = self.useTimestampsCheckbox.isChecked()
        if use_timestamps:
            timestamp_files = [self.timestampListWidget.item(i).text() for i in range(self.timestampListWidget.count())]
            if len(input_files) != len(timestamp_files):
                self.statusLabel.setText("Error: Number of input files and timestamp files/placeholders must match.")
                return
        else:
            timestamp_files = [None] * len(input_files)

        settings = {
            'db_threshold': self.dbThreshold.value(),
            'buffer_duration': self.bufferDuration.value(),
            'chunk_duration': self.chunkDuration.value(),
            'min_silence_factor': self.minSilenceFactor.value()
        }

        self.processButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.statusLabel.setText("Processing...")

        self.thread = ProcessThread(input_files, timestamp_files, settings)
        self.thread.progress.connect(self.updateProgress)
        self.thread.finished.connect(self.onProcessingFinished)
        self.thread.error.connect(self.onProcessingError)
        self.thread.start()

    def updateProgress(self, value, message):
        self.progressBar.setValue(value)
        self.statusLabel.setText(message)

    def onProcessingFinished(self):
        self.statusLabel.setText("Processing completed successfully!")
        self.processButton.setEnabled(True)

    def onProcessingError(self, error_message):
        self.statusLabel.setText(f"Error: {error_message}")
        self.processButton.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BatchSilenceRemoverGUI()
    sys.exit(app.exec_())