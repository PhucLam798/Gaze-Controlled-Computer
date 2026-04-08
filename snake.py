import cv2
import time
import requests
import random
import numpy as np
import onnxruntime as ort
from PIL import Image
from pathlib import Path
from collections import OrderedDict, namedtuple
import pyautogui
import tkinter as tk
import os
import subprocess

# Calibration file
calibration_file = "calibration.txt"
with open(calibration_file, "w") as file:
    pass  # Clear file content

print(f"The content of {calibration_file} has been cleared.")

# Set up the main application window
root = tk.Tk()
root.title("Box Animation")

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Create a canvas to fill the screen
canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg="black")
canvas.pack()

# Box properties
box_size = 120
box_color = "orange"
horizontal_speed = 15  # Smooth speed for left/right movement
downward_step = 100  # Larger downward step size for moving down smoothly
pause_time = 1.5  # Pause time at corners

# Initial position: Center of the screen
x_start = (screen_width - box_size) // 2
y_start = (screen_height - box_size) // 2
x_end, y_end = x_start + box_size, y_start + box_size
box = canvas.create_rectangle(x_start, y_start, x_end, y_end, fill=box_color)

cx, cy = 0, 0


def move_smoothly_to_corner():
    global cx, cy

    """ Moves the box smoothly from center to the top-left corner. """
    current_x, current_y = x_start, y_start

    while current_x > 0 or current_y > 0:
        step_x = min(horizontal_speed, current_x)
        step_y = min(horizontal_speed, current_y)

        canvas.move(box, -step_x, -step_y)
        root.update()
        time.sleep(0.02)

        # Get current position
        x1, y1, x2, y2 = canvas.coords(box)

        # Convert canvas coordinates to screen coordinates
        canvas_offset_x = canvas.winfo_rootx()
        canvas_offset_y = canvas.winfo_rooty()
        box_center = (
            (x1 + x2) // 2 + canvas_offset_x,
            (y1 + y2) // 2 + canvas_offset_y
        )

        formatted_data = f"Box: ({box_center[0]}, {box_center[1]}), Pupil: ({cx}, {cy})\n"
        print(formatted_data)
        with open(calibration_file, "a") as file:
            file.write(formatted_data)

        current_x -= step_x
        current_y -= step_y

def move_box():
    root.update()
    time.sleep(pause_time)  # Pause at center

    # Move smoothly to the top-left corner
    move_smoothly_to_corner()
    time.sleep(pause_time)  # Pause at top-left corner

    x_direction = horizontal_speed
    y_direction = 0  # Start moving horizontally

    while True:
        canvas.move(box, x_direction, y_direction)
        root.update()
        time.sleep(0.02)

        # Get current position
        x1, y1, x2, y2 = canvas.coords(box)

        # Convert canvas coordinates to screen coordinates
        canvas_offset_x = canvas.winfo_rootx()
        canvas_offset_y = canvas.winfo_rooty()
        box_center = (
            (x1 + x2) // 2 + canvas_offset_x,
            (y1 + y2) // 2 + canvas_offset_y
        )

        formatted_data = f"Box: ({box_center[0]}, {box_center[1]}), Pupil: ({cx}, {cy})\n"
        print(formatted_data)
        with open(calibration_file, "a") as file:
            file.write(formatted_data)

        # Detect when reaching a corner and pause
        if (x1 <= 0 and y1 <= 0) or (x2 >= screen_width and y1 <= 0) or (x2 >= screen_width and y2 >= screen_height - downward_step) or (x1 <= 15 and y2 >= screen_height - downward_step):
            time.sleep(pause_time)

        # Exit
        if x2 >= screen_width and y2 >= screen_height - downward_step:
            root.destroy()
            os._exit(0)

        # Smooth downward movement with a larger step
        if (x2 >= screen_width and x_direction > 0) or (x1 <= 0 and x_direction < 0):
            x_direction = 0  # Stop horizontal movement
            for _ in range(downward_step // horizontal_speed):  # Move smoothly downward
                canvas.move(box, 0, horizontal_speed)
                root.update()
                time.sleep(0.02)
            x_direction = horizontal_speed if x1 <= 0 else -horizontal_speed  # Change horizontal direction

move_box()
root.mainloop()
