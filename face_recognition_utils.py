import face_recognition
import cv2
import numpy as np
from datetime import datetime

def find_encodings(images):
    """
    Generate face encodings for a list of images
    """
    encode_list = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        encode = face_recognition.face_encodings(img)[0]
        encode_list.append(encode)
    return encode_list

def mark_attendance(name):
    """
    Mark attendance in the CSV file
    """
    with open('Attendance_Sheet.csv', 'r+') as f:
        my_data_list = f.readlines()
        name_list = []
        for line in my_data_list:
            entry = line.split(',')
            name_list.append(entry[0])
        if name not in name_list:
            now = datetime.now()
            dt_string = now.strftime('%H:%M:%S')
            d_str = now.strftime('%d:%m:%Y')
            f.writelines(f'\n{name},{dt_string},{d_str}')