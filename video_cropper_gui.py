#!/usr/bin/env python
"""
video_cropper_gui.py

This GUI application allows you to crop one or more videos into multiple parts.
Users can select multiple input videos and define the crop parameters (name, x-offset, y-offset, width, height)
via a table. Output files are saved in the same folder as the source video with file names like:
    {source_video_basename}_{crop_name}.mp4
"""

import os
import sys
import subprocess
import json

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QListWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QProgressBar, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Helper methods (similar to command-line version)

def get_video_dimensions(input_file):
    """
    Uses ffprobe to extract the video width and height
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_entries", "stream=index,codec_type,width,height,rotation:stream_tags=rotate",
        "-select_streams", "v:0",
        input_file
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        if "streams" not in data or not data["streams"]:
            raise ValueError("No video stream found.")

        # Extract primary width/height
        stream_info = data["streams"][0]
        width = stream_info.get("width", None)
        height = stream_info.get("height", None)
        if not (width and height):
            raise ValueError("Could not determine video width/height.")

        return width, height
    except Exception as e:
        raise RuntimeError(f"Error retrieving video dimensions (considering rotation): {e}")

def get_output_file(input_file, crop_name):
    """
    Constructs the output file path given the input file and crop name.
    """
    directory, filename = os.path.split(input_file)
    base, _ = os.path.splitext(filename)
    output_filename = f"{base}_{crop_name}.mp4"
    return os.path.join(directory, output_filename)

# Worker Thread for processing video crops

class VideoCropperWorker(QThread):
    logMessage = pyqtSignal(str)
    progressUpdate = pyqtSignal(int)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, input_videos, crop_definitions):
        """
        input_videos: List of input video file paths.
        crop_definitions: List of dictionaries; each dict has keys:
                          'name', 'x', 'y', 'width', 'height' (all numeric values as needed).
        """
        super().__init__()
        self.input_videos = input_videos
        self.crop_definitions = crop_definitions

    def run(self):
        total_tasks = len(self.input_videos) * len(self.crop_definitions)
        completed_tasks = 0

        for video in self.input_videos:
            try:
                video_width, video_height = get_video_dimensions(video)
                self.logMessage.emit(f"Processing video: {video} (Dimensions: {video_width}x{video_height})")
            except Exception as e:
                self.errorOccurred.emit(str(e))
                continue  # skip this video

            for crop in self.crop_definitions:
                crop_name = crop['name']
                # Validate crop bounds against video dimensions
                if crop['x'] < 0 or crop['y'] < 0:
                    self.errorOccurred.emit(f"Crop '{crop_name}' has negative x or y offset. Skipping.")
                    completed_tasks += 1
                    self.progressUpdate.emit(int(100 * completed_tasks / total_tasks))
                    continue
                if crop['width'] <= 0 or crop['height'] <= 0:
                    self.errorOccurred.emit(f"Crop '{crop_name}' must have positive width and height. Skipping.")
                    completed_tasks += 1
                    self.progressUpdate.emit(int(100 * completed_tasks / total_tasks))
                    continue
                if crop['x'] + crop['width'] > video_width:
                    self.errorOccurred.emit(
                        f"Crop '{crop_name}' exceeds video width (x + width = {crop['x'] + crop['width']} > {video_width}). Skipping."
                    )
                    completed_tasks += 1
                    self.progressUpdate.emit(int(100 * completed_tasks / total_tasks))
                    continue
                if crop['y'] + crop['height'] > video_height:
                    self.errorOccurred.emit(
                        f"Crop '{crop_name}' exceeds video height (y + height = {crop['y'] + crop['height']} > {video_height}). Skipping."
                    )
                    completed_tasks += 1
                    self.progressUpdate.emit(int(100 * completed_tasks / total_tasks))
                    continue

                output_file = get_output_file(video, crop_name)
                crop_filter = f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']}"
                cmd = [
                    "ffmpeg",
                    "-i", video,
                    "-filter:v", crop_filter,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "23",
                    "-c:a", "copy",
                    output_file,
                    "-y"  # Overwrite if exists
                ]
                self.logMessage.emit(f"Running crop '{crop_name}' for video '{os.path.basename(video)}' with filter: {crop_filter}")
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.logMessage.emit(f"Crop '{crop_name}' created successfully at: {output_file}")
                except subprocess.CalledProcessError as e:
                    self.errorOccurred.emit(f"Error processing crop '{crop_name}' for video '{video}': {e}")
                completed_tasks += 1
                self.progressUpdate.emit(int(100 * completed_tasks / total_tasks))
        self.logMessage.emit("Processing complete.")

# Main GUI Application

class VideoCropperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Cropper GUI")
        self.resize(800, 600)
        self.initUI()
        self.worker = None

    def initUI(self):
        main_layout = QVBoxLayout()

        # Input Videos Section
        input_layout = QHBoxLayout()
        input_btn_layout = QVBoxLayout()  # New vertical layout for video control buttons
        self.addVideosButton = QPushButton("Add Videos")
        self.addVideosButton.clicked.connect(self.selectVideos)
        self.removeVideosButton = QPushButton("Remove Selected Videos")
        self.removeVideosButton.clicked.connect(self.removeSelectedVideos)
        input_btn_layout.addWidget(self.addVideosButton)
        input_btn_layout.addWidget(self.removeVideosButton)
        input_btn_layout.addStretch()  # Add stretch to keep buttons at the top
        input_layout.addLayout(input_btn_layout)
        self.videoListWidget = QListWidget()
        self.videoListWidget.setSelectionMode(QListWidget.ExtendedSelection)  # Allow multiple selection
        input_layout.addWidget(self.videoListWidget)
        main_layout.addLayout(input_layout)

        # Crop Definitions Section
        crop_layout = QVBoxLayout()
        crop_label = QLabel("Crop Definitions (Name, X Offset, Y Offset, Width, Height):")
        crop_layout.addWidget(crop_label)
        self.cropTable = QTableWidget(0, 5)
        self.cropTable.setHorizontalHeaderLabels(["Name", "X Offset", "Y Offset", "Width", "Height"])
        crop_layout.addWidget(self.cropTable)
        # Buttons to add and remove crop rows:
        crop_btn_layout = QHBoxLayout()
        self.addCropButton = QPushButton("Add Crop")
        self.addCropButton.clicked.connect(self.addCropRow)
        self.removeCropButton = QPushButton("Remove Selected Crop")
        self.removeCropButton.clicked.connect(self.removeSelectedCropRow)
        crop_btn_layout.addWidget(self.addCropButton)
        crop_btn_layout.addWidget(self.removeCropButton)
        crop_layout.addLayout(crop_btn_layout)
        main_layout.addLayout(crop_layout)

        # Pre-fill with common examples (optional)
        self.prefillCrops()

        # Control Section: Run button and progress bar
        ctrl_layout = QHBoxLayout()
        self.runButton = QPushButton("Run")
        self.runButton.clicked.connect(self.runProcessing)
        ctrl_layout.addWidget(self.runButton)
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        ctrl_layout.addWidget(self.progressBar)
        main_layout.addLayout(ctrl_layout)

        # Log / Output Section
        self.logTextEdit = QTextEdit()
        self.logTextEdit.setReadOnly(True)
        main_layout.addWidget(QLabel("Log Output:"))
        main_layout.addWidget(self.logTextEdit)

        self.setLayout(main_layout)
    
    def prefillCrops(self):
        """
        Optionally pre-fill the crop definitions with common examples.
        """
        common_crops = [
            {"name": "1",   "x": "0",    "y": "480", "width": "540", "height": "960"},
            {"name": "2", "x": "540",  "y": "480", "width": "540", "height": "960"},
            {"name": "3",  "x": "1080", "y": "480", "width": "540", "height": "960"},
            {"name": "4",  "x": "1620", "y": "480", "width": "540", "height": "960"}
        ]
        for crop in common_crops:
            row_count = self.cropTable.rowCount()
            self.cropTable.insertRow(row_count)
            self.cropTable.setItem(row_count, 0, QTableWidgetItem(crop["name"]))
            self.cropTable.setItem(row_count, 1, QTableWidgetItem(crop["x"]))
            self.cropTable.setItem(row_count, 2, QTableWidgetItem(crop["y"]))
            self.cropTable.setItem(row_count, 3, QTableWidgetItem(crop["width"]))
            self.cropTable.setItem(row_count, 4, QTableWidgetItem(crop["height"]))

    def selectVideos(self):
        """
        Opens a file dialog to select one or more video files.
        """
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", "", "Video Files (*.mp4 *.avi *.mov)")
        if files:
            existing_files = set()
            for index in range(self.videoListWidget.count()):
                existing_files.add(self.videoListWidget.item(index).text())
            new_files = [f for f in files if f not in existing_files]
            if new_files:
                self.videoListWidget.addItems(new_files)
            else:
                QMessageBox.information(self, "Info", "All selected videos are already in the list.")

    def addCropRow(self):
        """
        Adds an empty new row to the crop table.
        """
        row_count = self.cropTable.rowCount()
        self.cropTable.insertRow(row_count)
        # Optionally, you may fill with default values:
        self.cropTable.setItem(row_count, 0, QTableWidgetItem(""))
        self.cropTable.setItem(row_count, 1, QTableWidgetItem("0"))
        self.cropTable.setItem(row_count, 2, QTableWidgetItem("0"))
        self.cropTable.setItem(row_count, 3, QTableWidgetItem("0"))
        self.cropTable.setItem(row_count, 4, QTableWidgetItem("0"))

    def removeSelectedCropRow(self):
        """
        Removes the currently selected row(s) in the crop table.
        """
        selected_ranges = self.cropTable.selectedRanges()
        rows_to_remove = set()
        for sel in selected_ranges:
            for row in range(sel.topRow(), sel.bottomRow() + 1):
                rows_to_remove.add(row)
        for row in sorted(rows_to_remove, reverse=True):
            self.cropTable.removeRow(row)

    def removeSelectedVideos(self):
        """
        Removes the selected videos from the list.
        """
        selected_items = self.videoListWidget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please select videos to remove.")
            return
        
        for item in selected_items:
            self.videoListWidget.takeItem(self.videoListWidget.row(item))

    def appendLog(self, message):
        """
        Appends a message to the log text area.
        """
        self.logTextEdit.append(message)

    def updateProgress(self, value):
        """
        Update the progress bar value.
        """
        self.progressBar.setValue(value)

    def runProcessing(self):
        """
        Reads the selected videos and crop definitions and starts the processing worker thread.
        """
        input_videos = []
        for i in range(self.videoListWidget.count()):
            input_videos.append(self.videoListWidget.item(i).text())

        if not input_videos:
            QMessageBox.warning(self, "Warning", "Please select at least one video file.")
            return

        # Gather crop definitions from the table.
        crop_definitions = []
        for row in range(self.cropTable.rowCount()):
            try:
                name_item = self.cropTable.item(row, 0)
                x_item = self.cropTable.item(row, 1)
                y_item = self.cropTable.item(row, 2)
                width_item = self.cropTable.item(row, 3)
                height_item = self.cropTable.item(row, 4)

                if not all([name_item, x_item, y_item, width_item, height_item]):
                    raise ValueError("All fields must be filled.")

                name = name_item.text().strip()
                x = int(x_item.text().strip())
                y = int(y_item.text().strip())
                width = int(width_item.text().strip())
                height = int(height_item.text().strip())
                if name == "":
                    raise ValueError("Crop name cannot be empty.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error in crop definition at row {row+1}: {e}")
                return
            crop_definitions.append({
                "name": name,
                "x": x,
                "y": y,
                "width": width,
                "height": height
            })

        if not crop_definitions:
            QMessageBox.warning(self, "Warning", "Please add at least one crop definition.")
            return

        # Disable the Run button to avoid re-entry
        self.runButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.logTextEdit.clear()
        self.appendLog("Starting processing...")

        # Instantiate and start the worker thread.
        self.worker = VideoCropperWorker(input_videos, crop_definitions)
        self.worker.logMessage.connect(self.appendLog)
        self.worker.progressUpdate.connect(self.updateProgress)
        self.worker.errorOccurred.connect(self.appendLog)
        self.worker.finished.connect(self.onProcessingFinished)
        self.worker.start()

    def onProcessingFinished(self):
        self.appendLog("All processing tasks completed.")
        QMessageBox.information(self, "Info", "All processing tasks completed.")
        self.runButton.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoCropperGUI()
    window.show()
    sys.exit(app.exec_())
