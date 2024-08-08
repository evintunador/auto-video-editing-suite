#!/bin/bash

# Change to the directory containing your script
cd /Users/evintunador/Documents/repos/video-silence-remover # /path/to/your/script/directory

# Activate your virtual environment
source venv/bin/activate

# Run the GUI script
python concatenator.py

# Deactivate the virtual environment when the GUI is closed
deactivate