import numpy as np
import cv2
import sys 
import os
import io
import json
from analyze_scenes import make_data_file, get_video_hash
import wave
import matplotlib
from time import time
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
PREDS_FOLDER = "preds_transformed/"
THRESHOLD = 0.5

brands = {
    "7f91457d3f5cc71141579e0afbe9a053": ["subway", "starbucks"],
    "1df718b7af04bd0fe044e35faf758aa1": ["nflnfl", "mcd"],
    "ff50d22b76b36cbb5ec0226069d26ad2":["ae", "hardrock"],
}

brands_to_ads = {
    "subway" : "dataset-001-001/dataset/Ads/Subway_Ad_15s",
    "starbucks" : "dataset-001-001/dataset/Ads/Starbucks_Ad_15s",
    "nflnfl" : "dataset-002-002/dataset2/Ads/nfl_Ad_15s",
    "mcd" : "dataset-002-002/dataset2/Ads/mcd_Ad_15s",
    "ae" : "dataset-003-003/dataset3/Ads/ae_Ad_15s",
    "hardrock" : "dataset-003-003/dataset3/Ads/hrc_Ad_15s",
}

if not os.path.exists(PREDS_FOLDER):
    print("Predictions folder does not exist")
    sys.exit(1)

def retrieve_formatted(hashh):
    predictions_formatted = {}
    predictions_formatted[hashh] = {}

    for pred in [x for x in os.listdir(PREDS_FOLDER) if "error" not in x]:
        with open(PREDS_FOLDER + pred, 'r') as fl:
            lines = fl.readlines()
            for line in lines:
                js = json.loads(line)

                filename = js["instance"]["content"]

                hash_vid = filename.split("video-")[-1].split("-")[0]
                if hash_vid != hashh:
                    continue
                frame_num = int(filename.split("frame")[-1].split(".png")[0])

                displays = js["prediction"]["displayNames"]
                confidences = js["prediction"]["confidences"]
                boxes = js["prediction"]["bboxes"]

                assert len(displays) == len(confidences)
                assert len(boxes) == len(displays)

                frame_preds = []

                for i in range(len(displays)):
                    if displays[i].lower() not in brands[hash_vid]:
                        continue
                    if confidences[i] < THRESHOLD:
                        continue
                    
                    frame_preds.append([displays[i], boxes[i]])
                
                if not video_num in predictions_formatted:
                    predictions_formatted[hash_vid] = {}
                
                if len(frame_preds) > 0:
                    predictions_formatted[hash_vid][frame_num] = frame_preds
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


def make_video(sourcefile, audiofile, out_file, out_audio, predictions_formatted, hashh):
    
    data_file = "temp.txt"

    ad_1 = []
    ad_2 = []

    with open(data_file, 'r') as f:
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
    prev_logo_name = ""
    i = 0
    processed_ad_1 = False
    processed_ad_2 = False
    while i < NUM_FRAMES:
        in_ad_1 = i >= ad_1[0] and i <= ad_1[1] 
        in_ad_2 = i >= ad_2[0] and i <= ad_2[1] 
        frame = get_next_frame(fb)
        for delta in range(0, LOOK_BACK_PREDS_FRAME + 1):
            if((i - delta) in predictions_formatted[hashh]):
                prev_logo_name = predictions_formatted[hashh][i-delta][0]
                overlay_predictions(frame, predictions_formatted[hashh][i-delta])
        frame_audio = audio_file.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE)
        
        if in_ad_1 or in_ad_2:
            print(prev_logo_name)
            if processed_ad_1 and in_ad_1:
                continue
            if processed_ad_2 and in_ad_2:
                continue
            
            if in_ad_1:
                processed_ad_1 = True
            elif in_ad_2:
                processed_ad_2 = True

            # add in the ad content
            ad_file = brands_to_ads[prev_logo_name]
            video_file_ad = open(ad_file + ".rgb", 'rb')
            fi_ad  = io.FileIO(video_file_ad.fileno())
            fb_ad = io.BufferedReader(fi_ad)
            frame_ad = get_next_frame(fb_ad)

            for qr in range(15 * VIDEO_FRAME_RATE):
                r = np.copy(frame_ad[:, :, 0])
                g = np.copy(frame_ad[:, :, 1])
                b = np.copy(frame_ad[:, :, 2])

                rgb_out.write(r.tobytes())
                rgb_out.write(g.tobytes())
                rgb_out.write(b.tobytes())

            ad_audio = wave.open(ad_file + ".wav", 'rb')
            ad_all_audio = audio_file.readframes(AUDIO_FRAME_RATE * 15) # 15s
            audio_out.writeframes(ad_all_audio)
            i += 1
            continue

        # add scene content
        r = np.copy(frame[:, :, 0])
        g = np.copy(frame[:, :, 1])
        b = np.copy(frame[:, :, 2])

        rgb_out.write(r.tobytes())
        rgb_out.write(g.tobytes())
        rgb_out.write(b.tobytes())
        audio_out.writeframes(frame_audio)

        i += 1

if __name__ == "__main__":
    start = time()
    sourcefile = sys.argv[1]
    audiofile = sys.argv[2]
    out_file = sys.argv[3]
    out_audio = sys.argv[4]
    hashh = get_video_hash(sourcefile)
    predictions_formatted = retrieve_formatted(hashh)
    make_data_file(sourcefile, hashh)
    make_video(sourcefile, audiofile, out_file, out_audio, predictions_formatted, hashh)
    print("PROCESSED IN", time() - start, "SECONDS")