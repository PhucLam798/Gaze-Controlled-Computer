import cv2
import time
import random
import numpy as np
import onnxruntime as ort
from PIL import Image
from pathlib import Path
import pyautogui
import tkinter as tk
import os
from pynput import keyboard
import re
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
import threading
from playsound import playsound
