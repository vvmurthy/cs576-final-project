import cv2
import sys
import analyze_scenes
import numpy as np
import io
import wave
from time import time
from analyze_scenes import make_data_file, get_video_hash
import os
import json

WIDTH = 480
HEIGHT = 270
NUM_FRAMES = 30 * 60 * 5 - 1
AUDIO_FRAME_RATE = 48000
VIDEO_FRAME_RATE = 30
BYTES_PER_FRAME_AUDIO = 2
LOOK_BACK_PREDS_FRAME = 2 
PREDS_FOLDER = "preds_transformed/"
THRESHOLD = 0.5

logos = {
    "7f91457d3f5cc71141579e0afbe9a053": ["Subway", "Starbucks"],
    "1df718b7af04bd0fe044e35faf758aa1": ["NFLNFL", "McD"],
    "ff50d22b76b36cbb5ec0226069d26ad2":["AE", "HardRock"],
    "0ab729e54aba8269827629f32b006c87" : ["Subway", "Starbucks"]
}

logoAd = {
    "Subway" : "dataset-001-001/dataset/Ads/Subway_Ad_15s",
    "Starbucks" : "dataset-001-001/dataset/Ads/Starbucks_Ad_15s",
    "NFLNFL" : "dataset-002-002/dataset2/Ads/nfl_Ad_15s",
    "McD" : "dataset-002-002/dataset2/Ads/mcd_Ad_15s",
    "AE" : "dataset-003-003/dataset3/Ads/ae_Ad_15s",
    "HardRock" : "dataset-003-003/dataset3/Ads/hrc_Ad_15s",
}

def getScenes(hash):

    scenes = []
    ads = []

    sceneFlag = False
    outputText = hash + ".txt"
    f = open(outputText, "r")

    lines = []
    for line in f:
        lines.append(line)

    for line in lines:
        if "ad" in line:
            if sceneFlag == True:
                end = line.split("-")[0]
                scenes.append([int(start), int(end)])
                sceneFlag = False
            adstart, adend = line.split(":")[0].split("-")
            ads.append([int(adstart), int(adend)])
        else:
            if sceneFlag == False:
                start = line.split("-")[0]
                sceneFlag = True
            if line == lines[-1]:
                end = line.split(":")[0].split("-")[1]
                scenes.append([int(start), int(end)])

    return scenes, ads

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

def write_next_frame(frame, outputVideoRGB):
    r = np.copy(frame[:, :, 0])
    g = np.copy(frame[:, :, 1])
    b = np.copy(frame[:, :, 2])

    outputVideoRGB.write(r.tobytes())
    outputVideoRGB.write(g.tobytes())
    outputVideoRGB.write(b.tobytes())

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
                    if displays[i] not in logos[hash_vid]:
                        continue
                    if confidences[i] < THRESHOLD:
                        continue
                    
                    frame_preds.append([displays[i], boxes[i]])
                
                if len(frame_preds) > 0:
                    predictions_formatted[hash_vid][frame_num] = frame_preds
    return predictions_formatted 

def edit_frame(frame, predictions):
    for preds in predictions:
        box = preds[1]
        display = preds[0]
        x = int(box[0] * WIDTH)
        y = int(box[2] * HEIGHT)
        x1 = int(box[1] * WIDTH)
        y1 = int(box[3] * HEIGHT)
        cv2.rectangle(frame, (x, y), (x1, y1), (0,0,255), 2)
        cv2.putText(frame, display, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    return display

def generate_final_video(inputVideo, inputAudio, outputVideo, outputAudio, predictions, hash):

    scenes, ads = getScenes(hash)

    videoFile = open(inputVideo, 'rb')
    fileIO  = io.FileIO(videoFile.fileno())
    fileBuffer = io.BufferedReader(fileIO)

    audioFile = wave.open(inputAudio, 'rb')

    outputVideoRGB = open(outputVideo, 'wb')

    outputAudioWave = wave.open(outputAudio, 'wb')
    outputAudioWave.setnchannels(1)
    outputAudioWave.setsampwidth(2)
    outputAudioWave.setframerate(AUDIO_FRAME_RATE)

    i = 0
    ad1Added = False
    ad2Added = False
    ad3Added = False
    detectedLogo = ""
    adsdetected = []

    while i < NUM_FRAMES:
        print(i)
        ad1 = i >= ads[0][0] and i <= ads[0][1] 
        ad2 = i >= ads[1][0] and i <= ads[1][1] 
        if len(ads) > 2:
            ad3 = i >= ads[2][0] and i <= ads[2][1] 
        else:
            ad3 = False

        frame = get_next_frame(fileBuffer)

        for delta in range(0, LOOK_BACK_PREDS_FRAME + 1):
            if((i - delta) in predictions[hash]):
                detectedLogo = edit_frame(frame, predictions[hash][i-delta])
        frameAudio = audioFile.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE)

        if ad1 or ad2 or ad3:
            if ad1Added and ad1:
                i += 1
                continue
            if ad2Added and ad2:
                i += 1
                continue
            if ad3Added and ad3:
                i += 1
                continue
            if detectedLogo == "":
                i += 1
                continue
            
            if ad1:
                ad1Added = True
            elif ad2:
                ad2Added = True
            elif ad3:
                ad3Added = True

            if detectedLogo not in adsdetected :
                adVideoFile = open(logoAd[detectedLogo] + ".rgb", 'rb')
                size = os.path.getsize(logoAd[detectedLogo] + ".rgb") 
                adVideoFrams = size // (HEIGHT * WIDTH * 3) - 1
                adVideoFileIO  = io.FileIO(adVideoFile.fileno())
                adVideoFileBuffer = io.BufferedReader(adVideoFileIO)
                adAudioFile = wave.open(logoAd[detectedLogo] + ".wav", 'rb')
            
                for f in range(adVideoFrams):
                    frameInAd = get_next_frame(adVideoFileBuffer)
                    write_next_frame(frameInAd, outputVideoRGB)
                    adAudio = adAudioFile.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE * adVideoFrams) 
                    outputAudioWave.writeframes(adAudio)
                i += 1
                adsdetected.append(detectedLogo)
                continue

            else :
                i += 1
                continue

        # add scene content
        write_next_frame(frame, outputVideoRGB)
        outputAudioWave.writeframes(frameAudio)

        i += 1


if __name__=="__main__":
    start = time()

    #taking arguments
    inputVideo = sys.argv[1]
    inputAudio = sys.argv[2]
    outputVideo = sys.argv[3]
    outputAudio = sys.argv[4]
    
    hash = get_video_hash(inputVideo)
    prediction = retrieve_formatted(hash)

    make_data_file(inputVideo, hash)

    generate_final_video(inputVideo, inputAudio, outputVideo, outputAudio, prediction, hash)

    print("Total time :", time()-start, "sec")