import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal

#class ProcessThread(QThread):
#    finished = pyqtSignal()
#    error = pyqtSignal(str)

#    def __init__(self, command):
#        QThread.__init__(self)
#        self.command = command

#    def run(self):
 #       try:
#            process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#            stdout, stderr = process.communicate()
#            if process.returncode != 0:
#                self.error.emit(stderr)
#            else:
 #               self.finished.emit()
#        except Exception as e:
 #           self.error.emit(str(e))

class ProcessThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    output = pyqtSignal(str)

    def __init__(self, command):
        QThread.__init__(self)
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in iter(process.stdout.readline, ''):
                self.output.emit(line.strip())
            process.stdout.close()
            return_code = process.wait()
            if return_code != 0:
                self.error.emit(f"Process exited with return code {return_code}")
            else:
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class SilenceRemoverGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input file selection
        self.inputFileButton = QPushButton('Select Input File')
        self.inputFileButton.clicked.connect(self.selectInputFile)
        self.inputFileLabel = QLabel('No file selected')
        layout.addWidget(self.inputFileButton)
        layout.addWidget(self.inputFileLabel)

        # Output file selection
        self.outputFileButton = QPushButton('Select Output File')
        self.outputFileButton.clicked.connect(self.selectOutputFile)
        self.outputFileLabel = QLabel('No file selected')
        layout.addWidget(self.outputFileButton)
        layout.addWidget(self.outputFileLabel)

        # Parameters
        paramLayout = QVBoxLayout()

        # DB Threshold
        dbLayout = QHBoxLayout()
        dbLayout.addWidget(QLabel('Decibel Threshold (dB):'))
        self.dbThreshold = QDoubleSpinBox()
        self.dbThreshold.setRange(-100, 0)
        self.dbThreshold.setValue(-45)
        self.dbThreshold.setDecimals(1)
        dbLayout.addWidget(self.dbThreshold)
        paramLayout.addLayout(dbLayout)

        # Buffer Duration
        bufferLayout = QHBoxLayout()
        bufferLayout.addWidget(QLabel('Buffer Duration (s):'))
        self.bufferDuration = QDoubleSpinBox()
        self.bufferDuration.setRange(0, 10)
        self.bufferDuration.setSingleStep(0.1)
        self.bufferDuration.setValue(0.2)
        bufferLayout.addWidget(self.bufferDuration)
        paramLayout.addLayout(bufferLayout)

        # Chunk Duration
        chunkLayout = QHBoxLayout()
        chunkLayout.addWidget(QLabel('Chunk Duration (s):'))
        self.chunkDuration = QSpinBox()
        self.chunkDuration.setRange(1, 3600)
        self.chunkDuration.setValue(150)
        chunkLayout.addWidget(self.chunkDuration)
        paramLayout.addLayout(chunkLayout)

        # Min Silence Factor
        silenceLayout = QHBoxLayout()
        silenceLayout.addWidget(QLabel('Min Silence Length (s):'))
        self.minSilenceFactor = QDoubleSpinBox()
        self.minSilenceFactor.setRange(0, 10)
        self.minSilenceFactor.setSingleStep(0.1)
        self.minSilenceFactor.setValue(0.6)
        silenceLayout.addWidget(self.minSilenceFactor)
        paramLayout.addLayout(silenceLayout)

        layout.addLayout(paramLayout)

        # Timestamps file selection
        self.timestampsFileButton = QPushButton('Select Input Timestamps File')
        self.timestampsFileButton.clicked.connect(self.selectTimestampsFile)
        self.timestampsFileLabel = QLabel('No file selected')
        layout.addWidget(self.timestampsFileButton)
        layout.addWidget(self.timestampsFileLabel)

        # Output timestamps file selection
        self.outputTimestampsFileButton = QPushButton('Select Output Timestamps File')
        self.outputTimestampsFileButton.clicked.connect(self.selectOutputTimestampsFile)
        self.outputTimestampsFileLabel = QLabel('No file selected')
        layout.addWidget(self.outputTimestampsFileButton)
        layout.addWidget(self.outputTimestampsFileLabel)

        # Process button
        self.processButton = QPushButton('Process Video')
        self.processButton.clicked.connect(self.processVideo)
        layout.addWidget(self.processButton)

        # Status label
        self.statusLabel = QLabel('Ready')
        layout.addWidget(self.statusLabel)

        # Terminal output
        self.terminalOutput = QTextEdit()
        self.terminalOutput.setReadOnly(True)
        layout.addWidget(QLabel('Terminal Output:'))
        layout.addWidget(self.terminalOutput)

        self.setLayout(layout)
        self.setWindowTitle('Silence Remover')
        self.show()

    def selectInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Input Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if filename:
            self.inputFileLabel.setText(filename)

    def selectOutputFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output Video File", "", "Video Files (*.mp4)")
        if filename:
            self.outputFileLabel.setText(filename)

    def selectTimestampsFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Input Timestamps File", "", "Text Files (*.txt)")
        if filename:
            self.timestampsFileLabel.setText(filename)

    def selectOutputTimestampsFile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output Timestamps File", "", "Text Files (*.txt)")
        if filename:
            self.outputTimestampsFileLabel.setText(filename)

    def processVideo(self):
        input_file = self.inputFileLabel.text()
        output_file = self.outputFileLabel.text()
        db_threshold = self.dbThreshold.value()
        buffer_duration = self.bufferDuration.value()
        chunk_duration = self.chunkDuration.value()
        min_silence_factor = self.minSilenceFactor.value()
        timestamps_file = self.timestampsFileLabel.text()
        output_timestamps_file = self.outputTimestampsFileLabel.text()

        if input_file == 'No file selected':
            self.statusLabel.setText("Please select an input file")
            return

        if output_file == 'No file selected':
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_no_silence{ext}"

        # Disable the process button
        self.processButton.setEnabled(False)
        self.statusLabel.setText("Processing...")

        # Prepare the command
        command = [
            'python', 'silence_remover.py',
            input_file,
            '-o', output_file,
            '-d', str(db_threshold),
            '-b', str(buffer_duration),
            '-c', str(chunk_duration),
            '-m', str(min_silence_factor)
        ]

        if timestamps_file != 'No file selected':
            command.extend(['-t', timestamps_file])

        if output_timestamps_file != 'No file selected':
            command.extend(['--output_timestamps', output_timestamps_file])

        # Create and start the processing thread
        #self.thread = ProcessThread(command)
        #self.thread.finished.connect(self.onProcessingFinished)
        #self.thread.error.connect(self.onProcessingError)
        #self.thread.start()

        # Clear previous output
        self.terminalOutput.clear()

        # Create and start the processing thread
        self.thread = ProcessThread(command)
        self.thread.finished.connect(self.onProcessingFinished)
        self.thread.error.connect(self.onProcessingError)
        self.thread.output.connect(self.updateTerminalOutput)
        self.thread.start()

    def onProcessingFinished(self):
        self.statusLabel.setText("Processing completed successfully!")
        self.processButton.setEnabled(True)

    def onProcessingError(self, error_message):
        self.statusLabel.setText(f"Error: {error_message}")
        self.processButton.setEnabled(True)

    def updateTerminalOutput(self, line):
        self.terminalOutput.append(line)
        self.terminalOutput.verticalScrollBar().setValue(self.terminalOutput.verticalScrollBar().maximum())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SilenceRemoverGUI()
    sys.exit(app.exec_())