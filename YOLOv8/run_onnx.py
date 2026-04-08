import cv2
import time
import requests
import random
import numpy as np
import onnxruntime as ort
from PIL import Image
from pathlib import Path
from collections import OrderedDict,namedtuple

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FPS, 30)

zoom_factor = 1.5

cx = 0
cy = 0

w = "best.onnx"

providers = ['CUDAExecutionProvider']
session = ort.InferenceSession(w, providers=providers)

def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleup=True, stride=32):
    shape = im.shape[:2]  
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup: 
        r = min(r, 1.0)
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1] 

    if auto:
        dw, dh = np.mod(dw, stride), np.mod(dh, stride) 

    dw /= 2  
    dh /= 2

    if shape[::-1] != new_unpad:  
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color) 
    return im, r, (dw, dh)

names = ['black pupil']
colors = {name:[random.randint(0, 255) for _ in range(3)] for i,name in enumerate(names)}

while True:

    start_time = time.time()

    ret, img = cap.read()
    

    if not ret:
        print("")
        break
   
    height, width, _ = img.shape
    
    center_x = int((width + width*0.35) // 2)
    center_y = int((height + height*0.35) // 2)

    radius_x = int(width*0.4)
    radius_y = int(height*0.4)


    cropped_frame = img[
        center_y - radius_y:center_y + radius_y,
        center_x - radius_x:center_x + radius_x
    ]

    img = cv2.resize(cropped_frame, (width, height))
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    image = img.copy()
    image, ratio, dwdh = letterbox(image, auto=False)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, 0)
    image = np.ascontiguousarray(image)

    im = image.astype(np.float32)
    im /= 255

    outname = [i.name for i in session.get_outputs()]

    inname = [i.name for i in session.get_inputs()]

    inp = {inname[0]:im}

    outputs = session.run(outname, inp)[0]

    ori_images = [img.copy()]

    for i,(batch_id,x0,y0,x1,y1,cls_id,score) in enumerate(outputs):
        image = ori_images[int(batch_id)]
        box = np.array([x0,y0,x1,y1])
        box -= np.array(dwdh*2)
        box /= ratio
        box = box.round().astype(np.int32).tolist()


        score = round(float(score),3)
        
        if score > 0.9:

            cx = (box[0] + box[2]) / 2  # x0, x1
            cy = (box[1] + box[3]) / 2  # y0, y1

            name = names[0]
            color = colors[name]
            name += ' '+str(score)
            cv2.rectangle(image,box[:2],box[2:],color,2)
            cv2.putText(image,name,(box[0], box[1] - 2),cv2.FONT_HERSHEY_SIMPLEX,0.75,[225, 255, 255],thickness=2)   

    image2 = Image.fromarray(ori_images[0])

    # image2.show()

    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


    cv2.imshow("Webcam", image_bgr)

    print(cx,cy)


    end_time = time.time()

    fps = 1 / (end_time - start_time)
    print(fps)

    if cv2.waitKey(1) & 0xFF == ord('q'):  
        break
    print("Running on:", ort.get_device())  


cap.release()
cv2.destroyAllWindows()
