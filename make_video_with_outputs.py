import numpy as np
import cv2
import sys 
import os
import io
import json
import wave
import matplotlib
import matplotlib.pyplot as plt
from os.path import exists

# video 1 2400 -> 2900 or so , 5500 -> 6000
# video 2 -> 0-452, 6000-6452
# video 3 -> the middle, the end
WIDTH = 480
HEIGHT = 270
NUM_FRAMES = 30 * 60 * 5

AUDIO_FRAME_RATE = 48000
VIDEO_FRAME_RATE = 30
BYTES_PER_FRAME_AUDIO = 2

LOOK_BACK_PREDS_FRAME = 2 # how many frames to look back in the event a pred does not exist for 
# the specified frame
PREDS_FOLDER = "preds/"
THRESHOLD = 0.5
brands = {
    1: ["subway", "starbucks"],
    2: ["nflnfl", "mcd"],
    3:["ae", "hardrock"],
}

if not os.path.exists(PREDS_FOLDER):
    print("Predictions folder does not exist")
    sys.exit(1)

def retrieve_formatted():
    predictions_formatted = {}

    for pred in [x for x in os.listdir(PREDS_FOLDER) if "error" not in x]:
        with open(PREDS_FOLDER + pred, 'r') as fl:
            lines = fl.readlines()
            for line in lines:
                js = json.loads(line)

                filename = js["instance"]["content"]

                video_num = int(filename.split("video-")[-1].split("-")[0])
                frame_num = int(filename.split("frame")[-1].split(".png")[0])

                displays = js["prediction"]["displayNames"]
                confidences = js["prediction"]["confidences"]
                boxes = js["prediction"]["bboxes"]

                assert len(displays) == len(confidences)
                assert len(boxes) == len(displays)

                frame_preds = []

                for i in range(len(displays)):
                    if displays[i].lower() not in brands[video_num]:
                        continue
                    if confidences[i] < THRESHOLD:
                        continue
                    
                    frame_preds.append([displays[i], boxes[i]])
                
                if not video_num in predictions_formatted:
                    predictions_formatted[video_num] = {}
                
                if len(frame_preds) > 0:
                    predictions_formatted[video_num][frame_num] = frame_preds
    return predictions_formatted

def get_next_frame(fb):
    r_frame = fb.read(WIDTH * HEIGHT)
    g_frame = fb.read(WIDTH * HEIGHT)
    b_frame = fb.read(WIDTH * HEIGHT)
    r_a = np.frombuffer(r_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 
    g_a = np.frombuffer(g_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 
    b_a = np.frombuffer(b_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 

    full_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    full_frame[:, :, 0] = r_a
    full_frame[:, :, 1] = g_a
    full_frame[:, :, 2] = b_a
    return full_frame

def overlay_predictions(frame, preds):
    for pr in preds:
        box = pr[1]
        disp = pr[0]
        x = int(box[0] * WIDTH)
        y = int(box[2] * HEIGHT)
        x1 = int(box[1] * WIDTH)
        y1 = int(box[3] * HEIGHT)
        cv2.rectangle(frame, (x, y), (x1, y1), (0,0,255), 2)
        display_text = disp.lower() 
        if disp.lower() == "nflnfl":
            display_text = "nfl"
        cv2.putText(frame, display_text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)


def make_video(BASE):
    sourcefile = BASE + "/Videos/data_test" + num + ".rgb"
    audiofile = BASE + "/Videos/data_test" + num + ".wav"
    out_file = BASE + "/Videos/data_test_modified" + num + ".rgb"
    out_audio = BASE + "/Videos/data_test_modified" + num + ".wav"
    output_file = BASE + "/Videos/data_test" + num + ".txt"

    ad_1 = []
    ad_2 = []

    predictions_formatted = retrieve_formatted()

    with open(output_file, 'r') as f:
        data_lines = f.readlines()
        for line in data_lines:
            if "ad" in line:
                first_num = int(line.split("-")[0])
                second_num = int(line.split("-")[-1].split(":")[0])

                if len(ad_1) == 0:
                    ad_1 = [first_num, second_num]
                elif len(ad_2) == 0:
                    ad_2 = [first_num, second_num]

    # cut up the video
    video_file = open(sourcefile, 'rb')
    fi  = io.FileIO(video_file.fileno())
    fb = io.BufferedReader(fi)

    audio_file = wave.open(audiofile, 'rb')


    rgb_out = open(out_file, 'wb')
    

    audio_out = wave.open(out_audio, 'wb')
    audio_out.setnchannels(1)
    audio_out.setsampwidth(2)
    audio_out.setframerate(AUDIO_FRAME_RATE)
    for i in range(NUM_FRAMES):
        in_ad_1 = i >= ad_1[0] and i <= ad_1[1] 
        in_ad_2 = i >= ad_2[0] and i <= ad_2[1] 
        frame = get_next_frame(fb)
        for delta in range(0, LOOK_BACK_PREDS_FRAME + 1):
            if((i - delta) in predictions_formatted[int(num)]):
                overlay_predictions(frame, predictions_formatted[int(num)][i-delta])
        frame_audio = audio_file.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE)
        
        if in_ad_1 or in_ad_2:
            continue
        r = np.copy(frame[:, :, 0])
        g = np.copy(frame[:, :, 1])
        b = np.copy(frame[:, :, 2])

        rgb_out.write(r.tobytes())
        rgb_out.write(g.tobytes())
        rgb_out.write(b.tobytes())
        audio_out.writeframes(frame_audio)

for num in ["1", "2", "3"]:
    base = "dataset-00" + num + "-00" + num + "/dataset"
    if num != "1":
        base = "dataset-00" + num + "-00" + num + "/dataset" + num 
    make_video(base)