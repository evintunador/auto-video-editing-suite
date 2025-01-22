import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

def select_input_file():
    """Prompt user to pick an input .mp4 file."""
    file_path = filedialog.askopenfilename(
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
    )
    if file_path:
        input_file_var.set(file_path)

def select_output_file():
    """Prompt user to pick an output .mp4 file."""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
    )
    if file_path:
        output_file_var.set(file_path)

def convert_volume():
    """Run ffmpeg to change the volume of the selected file."""
    input_file = input_file_var.get()
    output_file = output_file_var.get()
    volume_value = volume_var.get()

    if not input_file or not output_file or not volume_value:
        messagebox.showerror("Error", "Please select input, output, and volume.")
        return

    try:
        float(volume_value)  # Validate volume is a number
    except ValueError:
        messagebox.showerror("Error", "Volume must be a valid number.")
        return

    # Construct the ffmpeg command
    command = [
        "ffmpeg",
        "-i", input_file,
        "-filter:a", f"volume={volume_value}",
        output_file
    ]

    try:
        subprocess.run(command, check=True)
        messagebox.showinfo("Success", f"Output file created at:\n{output_file}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"ffmpeg failed with error code {e.returncode}")

# Create the Tkinter window
root = tk.Tk()
root.title("Volume Adjuster for MP4")

# Variables to store user inputs
input_file_var = tk.StringVar()
output_file_var = tk.StringVar()
volume_var = tk.StringVar()

# GUI layout
tk.Label(root, text="Input File:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=input_file_var, width=40).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse...", command=select_input_file).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Output File:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=output_file_var, width=40).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse...", command=select_output_file).grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="Volume Factor (e.g., 1.5):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
tk.Entry(root, textvariable=volume_var, width=10).grid(row=2, column=1, padx=10, pady=10, sticky="w")

tk.Button(root, text="Convert", command=convert_volume).grid(row=3, column=0, columnspan=3, pady=20)

root.mainloop()
