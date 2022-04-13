import numpy as np
import cv2
import sys 
import os
import io
import matplotlib
import matplotlib.pyplot as plt

WIDTH = 480
HEIGHT = 270
NUM_FRAMES = 30 * 60 * 5

num = "3"
BASE = "dataset-00" + num + "-00" + num + "/dataset" + num
sourcefile = BASE + "/Videos/data_test" + num + ".rgb"

brands = [BASE + "/Brand Images/" + x for x in os.listdir(BASE + "/Brand Images") if ".rgb" in x]
brands = sorted(brands)

assert len(brands) == 2

def get_ad_image(fl)
    video_file = open(fl, 'rb')
    fi  = io.FileIO(video_file.fileno())
    fb = io.BufferedReader(fi)
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

brand_1 = get_ad_image(brands[0])
brand_2 = get_ad_image(brands[1])

video_file = open(sourcefile, 'rb')
fi  = io.FileIO(video_file.fileno())
fb = io.BufferedReader(fi)

def get_next_frame():
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
    full_frame = np.mean(full_frame, axis=-1)
    return full_frame

deltas = []
indices = []
previous = get_next_frame()
previous = cv2.blur(previous, ksize=(3, 3))
index = 0
skip_frame = 3
#fourcc = cv2.VideoWriter_fourcc(*'MP4V')
#out = cv2.VideoWriter('output.mp4', fourcc, 1.0, (WIDTH,HEIGHT))

SEGMENTS_HORIZONTAL = 8
SEGMENTS_VERTICAL = 4

def find_closest_match(segment, prev_frame, segment_i, segment_j):

    start_i = max(0, (segment_i -1) * segment.shape[0])
    end_i = min(prev_frame.shape[0] - segment.shape[0], (segment_i + 1) * segment.shape[0])
    
    start_j = max(0, (segment_j -1) * segment.shape[1])
    end_j = min(prev_frame.shape[1] - segment.shape[1], (segment_j + 1) * segment.shape[1])

    min_error = 255 * segment.shape[0] * segment.shape[1] * 3
    min_error_segment = None
    for i in range(start_i, end_i, 3):
        for j in range(start_j, end_j, 3):
            slices = prev_frame[i : i + segment.shape[0], j : j + segment.shape[1]]
            error = np.sum(np.abs(segment - slices))
            if error < min_error:
                min_error = error
                min_error_segment = slices
    return min_error_segment


threshold = 20
indices_high_diff = []
while index < (NUM_FRAMES - 2):
    if index % 1 == 0:
        print("Processing", index)

    if skip_frame > 0:
        has_skipped = 0
        while has_skipped < skip_frame and index < (NUM_FRAMES - 2):
            nx = get_next_frame()
            has_skipped += 1
            index += 1
    

    if index >= (NUM_FRAMES - skip_frame):
        break
    
    nx = get_next_frame()
    index+=1
    nx = cv2.blur(nx,  ksize=(3, 3))
    xx = np.zeros(nx.shape, dtype=np.uint8)
    
    for i in range(SEGMENTS_VERTICAL):
        for j in range(SEGMENTS_HORIZONTAL):
            segment_height =int( HEIGHT / SEGMENTS_VERTICAL)
            segment_width = int(WIDTH / SEGMENTS_HORIZONTAL)
            segment = nx[i * segment_height : i * segment_height + segment_height, j * segment_width : j * segment_width + segment_width]
            findd = find_closest_match(segment, previous, i, j)
            xx[i * segment_height : i * segment_height + segment_height, j * segment_width : j * segment_width + segment_width] = findd
        
    diff  = np.abs(nx - xx)
    cv2.imwrite("temp2"  + num + "/" + str(index) + ".png", diff)
    diff[diff < threshold] = 0
    diff[diff > threshold] = 255

    diff_count = np.count_nonzero(diff)
    is_high_difference = diff_count > 0.5 * WIDTH * HEIGHT
    if is_high_difference:
        print(str(index) + " " + str(is_high_difference))
        indices_high_diff.append(index)
    

    delta = diff_count / (WIDTH * HEIGHT)

    deltas.append(delta)
    indices.append(index)
    previous = nx
plt.plot(indices, deltas)
plt.savefig('save2' +num  + '.png')



with open("data2" + num + ".txt", 'w') as f:

    # write add or normal
    # add threshold = 300 frames or less in a scene
    AD_LENGTH_THRESHOLD = 30 * 10
    for i in range(len(indices_high_diff) - 1):
        if indices_high_diff[i + 1] - indices_high_diff[i] < AD_LENGTH_THRESHOLD:
            f.write(str(indices_high_diff[i]) + "-" + str(indices_high_diff[i + 1]) + ": ad\n")
        else:
            f.write(str(indices_high_diff[i]) + "-" + str(indices_high_diff[i + 1]) + ": scene\n")
    indices_high_diff = [str(x) for x in indices_high_diff]
    f.write(",".join(indices_high_diff) + "\n")
