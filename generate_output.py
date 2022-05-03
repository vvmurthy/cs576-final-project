import cv2
import detectionLogo
import sys
import analyze_scenes
import numpy as np
import io
import wave

WIDTH = 480
HEIGHT = 270
NUM_FRAMES = 30 * 60 * 5
AUDIO_FRAME_RATE = 48000
VIDEO_FRAME_RATE = 30

def getScenes(outputText):

    scenes = []
    ads = []

    sceneFlag = False
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

def get_predicted_logo(logosCount):
    if logosCount["subway"] > logosCount["starbuck"]:
        logoinvideo = "subway"
    else:
        logoinvideo = "starbuck"
    return logoinvideo
    

if __name__=="__main__":
    #taking arguments
    # inputVideo = "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Videos/data_test1.rgb"
    # inputAudio = "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Videos/data_test1.wav"
    # outputVideo = "outputVideo.rgb"
    # outputAudio = "outputAudio.wav"
    inputVideo = sys.argv[0]
    inputAudio = sys.argv[1]
    outputVideo = sys.argv[2]
    outputAudio = sys.argv[3]
    outputText = "data_test1.txt"

    # logos = {
    #     "logo1" : "./dataset-001-001/dataset/Brand Images/starbucks_logo.rgb",
    #     "logo2" : "./dataset-001-001/dataset/Brand Images/subway_logo.rgb"
    # }

    logos = {
        "subway" : "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/logo_detection/logos/subway.rgb",
        "starbuck" : "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Brand Images/starbucks_logo.rgb"
    }

    logoAdAudios = {
        "starbuck" : '/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Ads/Starbucks_Ad_15s.wav',
        "subway" : "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Ads/Subway_Ad_15s.wav"
    }

    logoads = {
        "starbuck" : "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Ads/Starbucks_Ad_15s.rgb",
        "subway" : "/Users/umanglahoti/Documents/Multimedia/cs576-final-project/dataset-001-001/dataset/Ads/Subway_Ad_15s.rgb"
    }

    logosCount = {
        "starbuck" : 0,
        "subway" : 0
    }

    # analyze_scenes.make_data_file(inputVideo, "dataset-002-002/dataset2", 2)
    scenes, ads = getScenes(outputText)

    videoFile = open(inputVideo, 'rb')
    fileIO  = io.FileIO(videoFile.fileno())
    fileBuffer = io.BufferedReader(fileIO)

    audioFile = wave.open(inputAudio, 'rb')

    outputVideoRGB = open(outputVideo, 'wb')

    outputAudioWave = wave.open(outputAudio, 'wb')
    outputAudioWave.setnchannels(1)
    outputAudioWave.setsampwidth(2)
    outputAudioWave.setframerate(AUDIO_FRAME_RATE)

    adAdded = False

    for i in range(NUM_FRAMES):
        print("Processing frame " + str(i))
        scene = True
        for ad in ads:
            if i >= ad[0] and i <= ad[1]:
                scene = False

        if scene:
            frame = get_next_frame(fileBuffer)

            logoname, imgframe = detectionLogo.detectImg(frame=frame, logos=logos, i=i)
            if logoname != "":
                logosCount[logoname] = logosCount.get(logoname) + 1

            write_next_frame(frame, outputVideoRGB)

            frame_audio = audioFile.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE)
            outputAudioWave.writeframes(frame_audio)

            adAdded = False

        else:
            if not adAdded:
                adInScene = get_predicted_logo(logosCount)

                videoFileAd = open(logoads[adInScene], 'rb')
                fileIOAd  = io.FileIO(videoFileAd.fileno())
                fileBufferAd = io.BufferedReader(fileIOAd)

                audioFileAd = wave.open(logoAdAudios[adInScene], 'rb')

                logosCount["subway"] = 0
                logosCount["starbuck"] = 0

                while fileBufferAd.peek():
                    frameAd = get_next_frame(fileBufferAd)
                    r = np.copy(frameAd[:, :, 0])
                    g = np.copy(frameAd[:, :, 1])
                    b = np.copy(frameAd[:, :, 2])

                    outputVideoRGB.write(r.tobytes())
                    outputVideoRGB.write(g.tobytes())
                    outputVideoRGB.write(b.tobytes())

                    frame_audio_ad = audioFileAd.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE)
                    outputAudioWave.writeframes(frame_audio_ad)

                adAdded = True

            frame = get_next_frame(fileBuffer)
            frame_audio = audioFile.readframes(AUDIO_FRAME_RATE // VIDEO_FRAME_RATE)

    print(logosCount)