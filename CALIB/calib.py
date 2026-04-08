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
import sys
from pynput import keyboard

# Calibration file
calibration_file = "calibration.txt"
# with open(calib file, "w") as tep:
#     pass  # Xóa nội dung tệp
# with open("calibration2.txt", "w") as tep:
#     pass  # Xóa nội dung tệp


# Thiết lập cửa sổ ứng dụng chính
root = tk.Tk()
root.title("Box Animation")
root.attributes('-fullscreen', True)


screen_width, screen_height = pyautogui.size()

canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg="black")
canvas.pack()

# Box properties
box_size = 115
box_color = "#fd6100"
horizontal_speed = 17  # Tốc độ mượt mà cho chuyển động trái/phải
downward_step = 100  # Kích thước bước đi xuống để di chuyển xuống mượt mà
pause_time = 1.0 

# Vị trí ban đầu: Giữa màn hình
x_start = (screen_width - box_size) // 2
y_start = (screen_height - box_size) // 2
x_end, y_end = x_start + box_size, y_start + box_size

box = canvas.create_rectangle(x_start, y_start, x_end, y_end, fill=box_color)

cx, cy = 0, 0

#di chuyển mượt tới góc
def move_smoothly_to_corner():
    global cx, cy

    """ Di chuyển hộp mượt mà từ trung tâm đến góc trên bên trái.  """
    current_x, current_y = x_start, y_start

    while current_x > 0 or current_y > 0:
        step_x = min(horizontal_speed, current_x)
        step_y = min(horizontal_speed, current_y)

        canvas.move(box, -step_x, -step_y)
        root.update()
        time.sleep(0.02)

        # Lấy vị trí hiện tại
        x1, y1, x2, y2 = canvas.coords(box)

        #Chuyển đổi tọa độ canvas sang tọa độ màn hình
        canvas_offset_x = canvas.winfo_rootx()
        canvas_offset_y = canvas.winfo_rooty()
        box_center = (
            (x1 + x2) // 2 + canvas_offset_x,
            (y1 + y2) // 2 + canvas_offset_y
        )
         # [phần lấy tọa độ và ghi log]
        formatted_data = f"Box: ({box_center[0]}, {box_center[1]}), Pupil: ({cx}, {cy})\n"
        print(formatted_data)
        with open(calibration_file, "a") as file:
            file.write(formatted_data)

        current_x -= step_x
        current_y -= step_y

def move_box():
    global want_exit

    root.update()
    time.sleep(pause_time)  # Dừng ở giữa

    # Di chuyển mượt mà đến góc trên bên trái
    move_smoothly_to_corner()
    time.sleep(pause_time) 

    x_direction = horizontal_speed
    y_direction = 0  # bắt đầu di chuyển theo chiều ngang

    listener = keyboard.Listener(on_press=on_press)
    listener.start()  # Start the listener in a non-blocking way

    while True:
        canvas.move(box, x_direction, y_direction)
        root.update()
        time.sleep(0.02)

        # lấy toạ độ
        x1, y1, x2, y2 = canvas.coords(box)

        # Chuyển đổi tọa độ canvas sang tọa độ màn hình
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

        #  Phát hiện ô vuông đến các góc màn hình
        if ((x1 <= 0 and y1 <= 0) or #góc trên bên trái
            (x2 >= screen_width and y1 <= 0) or#góc trên bên phải
            (x2 >= screen_width and y2 >= screen_height - downward_step) or #góc dưới bên phải
            (x1 <= 25  and y2 >= screen_height - downward_step)):# góc dưới bên trái
            time.sleep(pause_time)

        # Exit
        if x2 >= screen_width and y2 >= screen_height - downward_step:

            turn_off_camera()

            try:
                print("[INFO] Starting gaze.py...")
                subprocess.Popen(["python", "gaze.py"])
                print("[INFO] gaze.py started successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to start gaze.py: {e}")

            root.destroy()
            sys.exit(0)
        
        if want_exit == True:
            turn_off_camera()
            root.destroy()
            os._exit(0)

        # Di chuyển xuống mượt mà với bước lớn hơn
        if (x2 >= screen_width and x_direction > 0) or (x1 <= 0 and x_direction < 0):
            x_direction = 0  # Dừng chuyển động ngang
            for _ in range(downward_step // horizontal_speed):  # Di chuyển xuống mượt mà
                canvas.move(box, 0, horizontal_speed)
                root.update()
                time.sleep(0.02)
            x_direction = horizontal_speed if x1 <= 0 else -horizontal_speed  # Thay đổi hướng ngang



cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

zoom_factor = 1.5

cx = 0
cy = 0

w = "best.onnx"

providers = ['CUDAExecutionProvider']
session = ort.InferenceSession(w, providers=providers)

def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleup=True, stride=32):
    # Thay đổi kích thước và đệm ảnh trong khi đáp ứng các ràng buộc bội số của bước
    shape = im.shape[:2] # hình dạng hiện tại [chiều cao, chiều rộng]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Tỷ lệ tỷ lệ (mới / cũ)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # chỉ thu nhỏ, không phóng to (để có mAP val tốt hơn)
        r = min(r, 1.0)

    # Tính đệm
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    if auto:  # hình chữ nhật tối thiểu
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding

    dw /= 2  # chia đệm thành 2 bên
    dh /= 2

    if shape[::-1] != new_unpad:   # thay đổi kích thước
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # thêm viền

    return im, r, (dw, dh)

names = ['black pupil']
colors = {name:[random.randint(0, 255) for _ in range(3)] for i,name in enumerate(names)}

def process_video():

    global cx,cy

    while True:

        ret, img = cap.read()
        #img = cv2.flip(img, 1)

        if not ret:
            print("Failed to capture image from webcam.")
            break
        
        # Lấy tâm của khung hình
        height, width, _ = img.shape
        
        # Dịch chuyển tâm về phía trên bên phải
        shift_x = int(width * 0.1)  # dịch chuyển 10% sang phải
        shift_y = int(height * 0.1)   # dịch chuyển 10% lên trên

        # Tính toán tâm mới cho việc cắt
        center_x, center_y = width // 2 + shift_x, height // 2 - shift_y

        # Tính toán hộp cắt
        radius_x, radius_y = int(width // (2 * zoom_factor)), int(height // (2 * zoom_factor))

        # Cắt khung hình để phóng to vào phần trên bên phải
        cropped_frame = img[
            center_y - radius_y:center_y + radius_y,
            center_x - radius_x:center_x + radius_x
        ]
        # Thay đổi kích thước khung hình đã cắt về kích thước ban đầu
        img = cv2.resize(cropped_frame, (width, height))

        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        image = img.copy()
        image, ratio, dwdh = letterbox(image, auto=False)
        image = image.transpose((2, 0, 1))
        image = np.expand_dims(image, 0)
        image = np.ascontiguousarray(image)

        im = image.astype(np.float32)
        im /= 255
        # im.shape

        outname = [i.name for i in session.get_outputs()]
        # outname

        inname = [i.name for i in session.get_inputs()]
        # inname

        inp = {inname[0]:im}

        # ONNX inference
        outputs = session.run(outname, inp)[0]
        # print(outputs)


        ori_images = [img.copy()]

        for i,(batch_id,x0,y0,x1,y1,cls_id,score) in enumerate(outputs):
            image = ori_images[int(batch_id)]
            box = np.array([x0,y0,x1,y1])
            box -= np.array(dwdh*2)
            box /= ratio
            box = box.round().astype(np.int32).tolist()

            # cls_id = int(cls_id)
            score = round(float(score),3)
            
            if score > 0.9:
                # Calculate the center of the bounding box
                cx = (box[0] + box[2]) / 2  # x0, x1
                cy = (box[1] + box[3]) / 2  # y0, y1

                name = names[0]
                color = colors[name]
                name += ' '+str(score)
                cv2.rectangle(image,box[:2],box[2:],color,2)
                cv2.putText(image,name,(box[0], box[1] - 2),cv2.FONT_HERSHEY_SIMPLEX,0.75,[225, 255, 255],thickness=2) 

        # Assuming ori_images[0] is a numpy array containing your image data
        image2 = Image.fromarray(ori_images[0])

        # Display the image
        # image2.show()
        # Convert to BGR to display using OpenCV
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        cv2.imshow("Webcam", image_bgr)

        # Center of bounding box
        # print(cx,cy)

        # Wait for a key press to continue or break
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit the loop
            break

    
    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()

import threading
threading.Thread(target=process_video).start()

def turn_off_camera():
    global cap
    cap.release()
    cv2.destroyAllWindows()

want_exit = False
# Backspace for Exit
def on_press(key):
    global want_exit 
    try:
        if key == keyboard.Key.backspace:
            print('Backspace Detected')
            want_exit = True
    except AttributeError:
        pass

time.sleep(4)

# Start moving the box
move_box()

# Run the application
root.mainloop()
