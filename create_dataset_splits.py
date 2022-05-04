import numpy as np
import cv2
import sys 
import os
import json
import io
import matplotlib
import matplotlib.pyplot as plt
from os.path import exists

WIDTH = 480
HEIGHT = 270

NUM_FRAMES = 9000
SKIP_FRAME = 1

# Approximate frame start and end times for each video's ads
ad_2_1 = [2000, 2400]
ad_2_2 = [4000, 4600]

ad_1_1 = [1200,2300]
ad_1_2 = [4400,5500]

ad_3_1 = [1500, 2500]
ad_3_2 = [4800, 8500]


# ad times approximately
# 3200 - 3700
# 5500 - 6100
# 7300 - 7800
ad_4_1 = [1900, 3150]
ad_4_2 = [6000, 7300]

def get_next_frame(fb):
    r_frame = fb.read(WIDTH * HEIGHT)
    g_frame = fb.read(WIDTH * HEIGHT)
    b_frame = fb.read(WIDTH * HEIGHT)
    r_a = np.frombuffer(r_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 
    g_a = np.frombuffer(g_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 
    b_a = np.frombuffer(b_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 

    full_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    full_frame[:, :, 0] = b_a
    full_frame[:, :, 1] = g_a
    full_frame[:, :, 2] = r_a
    return full_frame

files_in_folder = 0
index = 0
lines = []

for num in ["1", "2", "3", "4"]:
    BASE = "dataset-00" + num + "-00" + num + "/dataset"
    if num != "1":
        BASE = "dataset-00" + num + "-00" + num + "/dataset" + num 

    sourcefile = BASE + "/Videos/data_test" + num + ".rgb"

    video_file = open(sourcefile, 'rb')
    
    
    fi  = io.FileIO(video_file.fileno())
    fb = io.BufferedReader(fi)
    i = 0
    try:
        while i < NUM_FRAMES:
            for _ in range(SKIP_FRAME):
                if i < NUM_FRAMES:
                    get_next_frame(fb)
                    i += 1

            if files_in_folder >= 10000:
                index += 1
                files_in_folder = 0
                dirr = "test_dataset" + str(index) + "/"
                
            
            dirr = "test_dataset" + str(index) + "/"
            if not os.path.exists(dirr):
                os.mkdir(dirr)
            frame = get_next_frame(fb)
            fll = "video-" + num + "-frame" + str(i) + ".png"

            in_vid_1 = (num == "1") and ((i >= ad_1_1[0] and i <= ad_1_1[1]) or (i >= ad_1_2[0] and i <= ad_1_2[1]))
            in_vid_2 = (num == "2") and ((i >= ad_2_1[0] and i <= ad_2_1[1]) or (i >= ad_2_2[0] and i <= ad_2_2[1]))
            in_vid_3 = (num == "3") and ((i >= ad_3_1[0] and i <= ad_3_1[1]) or (i >= ad_3_2[0] and i <= ad_3_2[1]))
            in_vid_4 = (num == "4") and ((i >= ad_4_1[0] and i <= ad_4_1[1]) or (i >= ad_4_2[0] and i <= ad_4_2[1]))

            if in_vid_1 or in_vid_2 or in_vid_3 or in_vid_4:
                assert cv2.imwrite(dirr + fll, frame)
                filename = "gs://s2022-cs576-bucket/" + fll
                lnn = "{\"content\": \"" + filename + "\", \"mimeType\": \"image/png\"}"
                lines.append(lnn + "\n")
                files_in_folder += 1

            i += 1
            
    except:
        print("Error Encountered")
        pass
csv_file = open("file_test.jsonl", 'w')
csv_file.writelines(lines)
