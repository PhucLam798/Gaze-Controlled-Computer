import pyautogui
import time
import threading
import tkinter as tk

# Định nghĩa vùng hoạt động (tọa độ và kích thước)
UP_BOX = {"x": 200, "y": 100, "width": 300, "height": 100}  # Vùng cuộn lên
DOWN_BOX = {"x": 200, "y": 250, "width": 300, "height": 100}  # Vùng cuộn xuống

# Biến lưu tốc độ cuộn
scroll_speed = 25  # Giá trị mặc định

def is_mouse_in_box(box):
    mouse_x, mouse_y = pyautogui.position()
    return (
        box["x"] <= mouse_x <= box["x"] + box["width"]
        and box["y"] <= mouse_y <= box["y"] + box["height"]
    )

def scroll(direction):
    global scroll_speed
    if direction == "up":
        pyautogui.scroll(scroll_speed)
    elif direction == "down":
        pyautogui.scroll(-scroll_speed)

def monitor_mouse():
    try:
        while True:
            if is_mouse_in_box(UP_BOX):
                scroll("up")
            elif is_mouse_in_box(DOWN_BOX):
                scroll("down")
            time.sleep(0.04)  # Giảm thời gian ngủ để cuộn mượt hơn
    except KeyboardInterrupt:
        print("Kết thúc chương trình.")

def draw_boxes(canvas):
    # Vẽ ô cuộn lên
    canvas.create_rectangle(
        UP_BOX["x"], UP_BOX["y"],
        UP_BOX["x"] + UP_BOX["width"], UP_BOX["y"] + UP_BOX["height"],
        outline="blue", width=2
    )
    canvas.create_text(
        UP_BOX["x"] + UP_BOX["width"] / 2,
        UP_BOX["y"] + UP_BOX["height"] / 2,
        text="Scroll Up", font=("Arial", 12), fill="blue"
    )

    # Vẽ ô cuộn xuống
    canvas.create_rectangle(
        DOWN_BOX["x"], DOWN_BOX["y"],
        DOWN_BOX["x"] + DOWN_BOX["width"], DOWN_BOX["y"] + DOWN_BOX["height"],
        outline="green", width=2
    )
    canvas.create_text(
        DOWN_BOX["x"] + DOWN_BOX["width"] / 2,
        DOWN_BOX["y"] + DOWN_BOX["height"] / 2,
        text="Scroll Down", font=("Arial", 12), fill="green"
    )

def update_scroll_speed(val):
    global scroll_speed
    scroll_speed = int(val)

def move_boxes(a, b):
    global UP_BOX, DOWN_BOX
    # Di chuyển ô cuộn lên
    UP_BOX["x"] += b
    UP_BOX["y"] += a
    # Di chuyển ô cuộn xuống
    DOWN_BOX["x"] += b
    DOWN_BOX["y"] += a

if __name__ == "__main__":
    # a (xuống) và b (ngang)
    a = 50  
    b = -50

    # Di chuyển các ô
    move_boxes(a, b)

    root = tk.Tk()
    root.title("Scroll Zones")

    # Đặt kích thước giao diện khớp với vùng scroll box sau khi di chuyển
    root.geometry(f"{DOWN_BOX['x'] + DOWN_BOX['width']}x{DOWN_BOX['y'] + DOWN_BOX['height']}+0+0")

    # Loại bỏ thanh viền của cửa sổ
    root.overrideredirect(True)

    # Làm trong suốt hoàn toàn (nền canvas)
    root.attributes("-topmost", True)  # Cửa sổ luôn nằm trên cùng
    root.attributes("-transparentcolor", "white")

    # Tạo canvas với nền trong suốt
    canvas = tk.Canvas(
        root,
        width=DOWN_BOX["x"] + DOWN_BOX["width"],
        height=DOWN_BOX["y"] + DOWN_BOX["height"],
        bg="white",  # Phần này sẽ được làm trong suốt
        highlightthickness=0
    )
    canvas.pack()

    # Vẽ các vùng cuộn
    draw_boxes(canvas)

    # Khởi chạy luồng theo dõi chuột
    mouse_thread = threading.Thread(target=monitor_mouse, daemon=True)
    mouse_thread.start()

    root.mainloop()