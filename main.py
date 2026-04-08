import cv2
import numpy as np
import pyautogui
import tkinter as tk
from tkinter import ttk, Frame, Label, BOTH, TOP, BOTTOM, LEFT, RIGHT, RAISED, X
from PIL import Image, ImageTk
import main1
import subprocess

# Khai báo biến toàn cục
current_camera = None
cap = None
screen_width, screen_height = pyautogui.size()
stop_camera_flag = False
aruco_active = False
marker_windows = []
keyboard_window = None
scroll_process = None
scroll_active = False

# Định nghĩa màu sắc giao diện bằng mã hex
BG_COLOR = "#2c3e50"
BUTTON_COLOR = "#3498db"
BUTTON_ACTIVE_COLOR = "#2980b9"
STOP_COLOR = "#e74c3c"
STOP_ACTIVE_COLOR = "#c0392b"
TEXT_COLOR = "#000000"
FRAME_COLOR = "#34495e"
ACTIVE_CAMERA_COLOR = "#2ecc71"
ARUCO_COLOR = "#9b59b6"
ARUCO_ACTIVE_COLOR = "#8e44ad"

def turn_off_camera():
    global current_camera, cap, stop_camera_flag
    stop_camera_flag = True
    
    if cap is not None:
        cap.release()
        cv2.destroyAllWindows()
        current_camera = None
        cap = None
        video_label.config(image='')
        video_label.image = ''
        status_label.config(text="Camera đã tắt", fg="red")
    
    btn_cam1.config(style="TButton")


def update_frame_cam1():
    global stop_camera_flag, cap
    s = 0.40
    if stop_camera_flag or cap is None or not cap.isOpened():
        return
        
    try:
        ret, frame = cap.read()
        if ret:
            height, width, _ = frame.shape

            center_x = int((width + width*0.35) // 2)
            center_y = int((height + height*0.35) // 2)

            radius_x = int(width*s)
            radius_y = int(height*s)

            cropped_frame = frame[
                center_y - radius_y:center_y + radius_y,
                center_x - radius_x:center_x + radius_x
            ]
            
            frame = cv2.resize(cropped_frame, (int(width - width*0.2), int(height - height*0.2)))
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
        
        if not stop_camera_flag and current_camera == 1:
            video_label.after(10, update_frame_cam1)
    except Exception as e:
        print(f"Lỗi khi đọc frame camera 1: {e}")
        turn_off_camera()

def start_camera(camera_index):
    global current_camera, cap, stop_camera_flag
    
    if current_camera == camera_index:
        turn_off_camera()
        status_label.config(text="Camera đã tắt", fg="red")
        return
    
    turn_off_camera()
    stop_camera_flag = False
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        status_label.config(text=f"Không thể mở camera {camera_index}", fg="red")
        return
    
    current_camera = camera_index
    status_label.config(text=f"Đang hiển thị Camera {camera_index}", fg="green")
    
    if camera_index == 1:
        btn_cam1.config(style="ActiveCamera.TButton")
        update_frame_cam1()

def stop_camera():
    global stop_camera_flag, cap, current_camera
    if cap is not None and cap.isOpened():
        turn_off_camera()
        status_label.config(text="Camera đã tắt", fg="red")
    else:
        status_label.config(text="Không có camera đang hoạt động", fg="yellow")

def open_virtual_keyboard():
    global keyboard_window
    if keyboard_window is not None and keyboard_window.winfo_exists():
        keyboard_window.destroy()
        keyboard_window = None
        status_label.config(text="Trạng thái: Bàn phím ảo đã tắt", fg="red")
        btn_keyboard.config(style="TButton")
        return
    
    keyboard_window = tk.Toplevel(win)
    keyboard_window.title("Bàn Phím Ảo")
    keyboard_app = main1.VirtualKeyboard(keyboard_window)
    
    screen_width, screen_height = pyautogui.size()
    keyboard_window.geometry(f"{screen_width}x{screen_height-40}+0+0")
    keyboard_window.resizable(True, True)
    status_label.config(text="Bàn phím ảo đang hoạt động", fg="green")
    btn_keyboard.config(style="ActiveCamera.TButton")

def scroll():
    global scroll_process, scroll_active
    if scroll_active:
        if scroll_process is not None:
            scroll_process.terminate()
            scroll_process = None
        scroll_active = False
        status_label.config(text="Scroll đã tắt", fg="red")
        btn_scroll.config(style="TButton")
        return
    
    try:
        scroll_process = subprocess.Popen(["python", "scroll.py"])
        scroll_active = True
        status_label.config(text="Scroll đang hoạt động", fg="green")
        btn_scroll.config(style="ActiveCamera.TButton")
    except Exception as e:
        status_label.config(text=f"Lỗi khi chạy scroll: {e}", fg="red")

def click():
    #with open('calibration.txt', 'w') as f: f.write('')
    subprocess.Popen(["python", "main2.py"])

def on_key(event):
    if event.keysym == 'q':
        turn_off_camera()
        if keyboard_window is not None and keyboard_window.winfo_exists():
            keyboard_window.destroy()
        if scroll_process is not None:
            scroll_process.terminate()
        for window in marker_windows:
            window.destroy()
        win.destroy()

# Tạo cửa sổ chính
win = tk.Tk()
win.geometry("1450x750")
win.title("Hệ Thống Giao Tiếp Và Điều Khiến Máy Tính")
win.configure(bg=BG_COLOR)

# Tạo khung tiêu đề
header_frame = Frame(win, height=80, bg=BG_COLOR)
header_frame.pack(fill=X, side=TOP)
header_label = Label(header_frame,
                   text="HỆ THỐNG HỖ TRỢ GIAO TIẾP VÀ ĐIỀU KHIẾN MÁY TÍNH",
                   font=("Arial", 24, "bold"),
                   fg=TEXT_COLOR,
                   bg=BG_COLOR)
header_label.pack(pady=20)

# Tạo khung chính
main_frame = Frame(win, bg=BG_COLOR)
main_frame.pack(fill=BOTH, expand=True, padx=40, pady=20)

# Tạo bảng điều khiển
control_frame = Frame(main_frame, bg=FRAME_COLOR, width=600, height=1000,
                     relief=RAISED, borderwidth=2)
control_frame.pack_propagate(False)
control_frame.pack(side=LEFT, padx=10, pady=10)

# Tạo khu vực hiển thị camera
camera_frame = Frame(main_frame, bg=FRAME_COLOR, width=900, height=600,
                    relief=RAISED, borderwidth=2)
camera_frame.pack_propagate(False)
camera_frame.pack(side=RIGHT, padx=20, pady=20)
video_label = Label(camera_frame, bg="black")
video_label.pack(fill=BOTH, expand=True)

# Tạo nhãn trạng thái
status_label = Label(control_frame,
                   text="Sẵn sàng",
                   font=("Arial", 18),
                   fg=TEXT_COLOR,
                   bg=FRAME_COLOR)
status_label.pack(pady=20)

# Cấu hình style cho các nút
style = ttk.Style()
style.configure("TButton",
               font=("Arial", 23),
               padding=15,
               width=15,
               background=BUTTON_COLOR,
               foreground=TEXT_COLOR)
style.map("TButton",
         background=[("active", BUTTON_ACTIVE_COLOR)],
         foreground=[("active", TEXT_COLOR)])

style.configure("Stop.TButton",
               background=STOP_COLOR,
               foreground=TEXT_COLOR)
style.map("Stop.TButton",
         background=[("active", STOP_ACTIVE_COLOR)],
         foreground=[("active", TEXT_COLOR)])

style.configure("ActiveCamera.TButton",
               background=ACTIVE_CAMERA_COLOR,
               foreground=TEXT_COLOR)
style.map("ActiveCamera.TButton",
         background=[("active", ACTIVE_CAMERA_COLOR)],
         foreground=[("active", TEXT_COLOR)])

style.configure("Aruco.TButton",
               background=ARUCO_COLOR,
               foreground=TEXT_COLOR)
style.map("Aruco.TButton",
         background=[("active", ARUCO_ACTIVE_COLOR)],
         foreground=[("active", TEXT_COLOR)])

# Tạo các nút điều khiển
btn_start = ttk.Button(control_frame, text="Bắt đầu", command=click, style="TButton")
btn_cam1 = ttk.Button(control_frame, text="Camera 1", command=lambda: start_camera(1), style="TButton")
btn_stop = ttk.Button(control_frame, text="Dừng Camera", command=stop_camera, style="Stop.TButton")
btn_scroll = ttk.Button(control_frame, text="Scroll", command=scroll, style="TButton")
btn_keyboard = ttk.Button(control_frame, text="Bàn Phím Ảo", command=open_virtual_keyboard, style="TButton")

btn_start.pack(pady=10, padx=20, fill=X)
btn_cam1.pack(pady=10, padx=20, fill=X)
btn_stop.pack(pady=10, padx=20, fill=X)
btn_scroll.pack(pady=10, padx=20, fill=X)
btn_keyboard.pack(pady=10, padx=20, fill=X)

# Tạo khung chân trang
footer_frame = Frame(win, height=40, bg=BG_COLOR)
footer_frame.pack(fill=X, side=BOTTOM)

win.bind("<KeyPress>", on_key)

win.mainloop()