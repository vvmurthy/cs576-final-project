import numpy as np
import cv2
import sys 
import os
import io
import hashlib
import matplotlib
import matplotlib.pyplot as plt
from os.path import exists

# video 1 2400 -> 2900 or so , 5500 -> 6000
# video 2 -> 0-452, 6000-6452
# video 3 -> the middle, the end
WIDTH = 480
HEIGHT = 270
NUM_FRAMES = 30 * 60 * 5
skip_frame = 3 # process every 4th frame

SEGMENTS_HORIZONTAL = 8
SEGMENTS_VERTICAL = 4

THRESHOLD = 50
PERCENT = 0.25

def get_video_hash(sourcefile):
    md5_hash = hashlib.md5()

    digest = ""
    with open(sourcefile, "rb") as a_file:
        content = a_file.read()
        md5_hash.update(content)

        digest = md5_hash.hexdigest()
    return digest

def get_ad_image(fl):
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


def create_rgb_hist(image):
    BINS = 16
    NORM_IMAGE_PIXELS = 1000000
    
    h, w, c = image.shape
    current_pixels = h * w
    rgbhist = np.zeros([(BINS+1) * BINS * BINS, 1], np.float32)
    bsize = 256 / BINS
    r = image[:, :, 0] / bsize
    g = image[:, :, 1] / bsize
    b = image[:, :, 2] / bsize

    assert np.max(r) < BINS
    assert np.max(g) < BINS
    assert np.max(b) < BINS

    indices = np.zeros([image.shape[0], image.shape[1]], dtype=np.float64)
    indices += (r * BINS * BINS)
    indices += (g * BINS)
    indices += (b)


    for val in np.unique(indices):
        count = np.count_nonzero(indices == val)
        rgbhist[int(val), 0] = int((count / current_pixels) * NORM_IMAGE_PIXELS)
    
    return rgbhist

def get_cropped_brand(brand):
    background_r = brand[10, 10, 0]
    background_g = brand[10, 10, 1]
    background_b = brand[10, 10, 2]

    thresh = np.zeros((brand.shape[0], brand.shape[1]), dtype=np.uint8)
    thresh[:, :] = 255
    thresh[brand[:, :, 0] != background_r] = 0
    thresh[brand[:, :, 1] != background_g] = 0
    thresh[brand[:, :, 2] != background_b] = 0
    thresh[thresh == 0] = 1
    thresh[thresh == 255] = 0
    thresh[thresh == 1] = 255

    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = 0
    cont = None
    for c in contours:
        rect = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        if area > largest_contour:
            largest_contour = area
            cont = c
    x,y,w,h = cv2.boundingRect(cont)
    brand_cropped = np.copy(brand)
    return brand_cropped[y : y + h , x : x + w, :]

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
    full_frame = np.mean(full_frame, axis=-1)
    img_resized = cv2.resize(full_frame, dsize=(WIDTH // 2, HEIGHT // 2), interpolation=cv2.INTER_CUBIC)
    return img_resized


def find_closest_match(segment, prev_frame, segment_i, segment_j):

    start_i = max(0, (segment_i -1) * segment.shape[0])
    end_i = min(prev_frame.shape[0] - segment.shape[0], (segment_i + 1) * segment.shape[0])
    
    start_j = max(0, (segment_j -1) * segment.shape[1])
    end_j = min(prev_frame.shape[1] - segment.shape[1], (segment_j + 1) * segment.shape[1])

    min_error = 255 * WIDTH * HEIGHT * 3
    min_error_segment = None
    for i in range(start_i, end_i, 3):
        for j in range(start_j, end_j, 3):
            slices = prev_frame[i : i + segment.shape[0], j : j + segment.shape[1]]
            error = np.sum(np.abs(segment - slices))
            if error < min_error:
                min_error = error
                min_error_segment = slices
    assert min_error_segment is not None
    return min_error_segment

"""

Main function of this file, designed to create a "data" file summarizing the 
scene cuts between images in the video

* does this through the diff_count method, which determines the segment-wise
difference between two images, a "previous" image and a "next" image
"""
def make_data_file(sourcefile, hashh):
    output_file = "temp.txt"
    secondary_cached_output = hashh + ".txt"

    if exists(secondary_cached_output):
        return True

    video_file = open(sourcefile, 'rb')
    fi  = io.FileIO(video_file.fileno())
    fb = io.BufferedReader(fi)

    deltas = []
    indices = []
    previous = get_next_frame(fb)
    index = 0

    indices_high_diff = [0,]
    difference_reads = np.zeros((NUM_FRAMES // (skip_frame + 1)), dtype=np.float32)
    while index < (NUM_FRAMES - 2):

        skips = []
        if skip_frame > 0:
            has_skipped = 0
            while has_skipped < skip_frame and index < (NUM_FRAMES - 2):
                nx = get_next_frame(fb)
                skips.append(nx)
                has_skipped += 1
                index += 1
        
        def get_diff_count(previous, nx):
            xx = np.zeros(nx.shape, dtype=np.uint8)
            for i in range(SEGMENTS_VERTICAL):
                for j in range(SEGMENTS_HORIZONTAL):
                    segment_height =int( nx.shape[0] / SEGMENTS_VERTICAL)
                    segment_width = int(nx.shape[1] / SEGMENTS_HORIZONTAL)
                    segment = nx[i * segment_height : i * segment_height + segment_height, j * segment_width : j * segment_width + segment_width]
                    findd = find_closest_match(segment, previous, i, j)
                    xx[i * segment_height : i * segment_height + segment_height, j * segment_width : j * segment_width + segment_width] = findd
                
            diff  = np.abs(nx - xx)
            diff[diff < THRESHOLD] = 0
            diff[diff > THRESHOLD] = 255
            diff_count = np.count_nonzero(diff)
            return diff_count
        
        def is_high_difference(diff_count, nx):
            return diff_count > PERCENT * nx.shape[0] * nx.shape[1]
    

        if index >= (NUM_FRAMES - skip_frame):
            break
        
        nx = get_next_frame(fb)
        index+=1
        skips.append(nx)

        diff_count = get_diff_count(previous, nx)
        is_high_diff = is_high_difference(diff_count, nx)

        difference_reads[index // (skip_frame + 1)] = diff_count / (nx.shape[0] * nx.shape[1])
        
        if is_high_diff:
            any_high_diff = False
            pr = np.copy(previous) 
            latest_index = index - len(skips)
            high_diff_last = latest_index
            for i in range(len(skips)):
                nextt = skips[i]
                diff_count = get_diff_count(pr, nextt)
                is_high_diff = is_high_difference(diff_count, nextt)
                if is_high_diff:
                    high_diff_last = latest_index
                any_high_diff = (any_high_diff or is_high_diff)
                pr = nextt
                latest_index += 1
            if any_high_diff:
                indices_high_diff.append(high_diff_last)
            is_high_diff = any_high_diff
        print(str(index) + " " + str(is_high_diff) + " " + str(diff_count / (nx.shape[0] * nx.shape[1])))
        

        delta = diff_count / (nx.shape[0] * nx.shape[1])

        deltas.append(delta)
        indices.append(index)
        previous = nx
    indices_high_diff.append(NUM_FRAMES)

    indices_high_diff_normed = [0,]
    indices.append(NUM_FRAMES)
    for q in range(0, 2000, 500):
        if q + 5000 < len(difference_reads):
            difference_reads[q:q + 500] -= np.mean(difference_reads[q : q + 500])
        else:
             difference_reads[q:] -= np.mean(difference_reads[q:])
    
    for i in range(len(difference_reads)):
        if difference_reads[i] > 0.18:
            indices_high_diff_normed.append(i * (skip_frame + 1))

    indices_high_diff_normed.append(NUM_FRAMES)

    with open(output_file, 'w') as f:

        # write add or normal
        # add threshold = 15s ad
        AD_LENGTH_THRESHOLD = 30 * 16
        for i in range(len(indices_high_diff_normed) - 1):
            if indices_high_diff_normed[i + 1] - indices_high_diff_normed[i] < AD_LENGTH_THRESHOLD:
                f.write(str(indices_high_diff_normed[i]) + "-" + str(indices_high_diff_normed[i + 1]) + ": ad\n")
            else:
                f.write(str(indices_high_diff_normed[i]) + "-" + str(indices_high_diff_normed[i + 1]) + ": scene\n")
        indices_high_diff_normed = [str(x) for x in indices_high_diff_normed]

    compress_down_scenes = []
    
    with open(output_file, 'r') as f:
        lines  = f.readlines()
        for line in lines:
            if "," not in line:
                first_num = int(line.split("-")[0])
                second_num = int(line.split("-")[-1].split(":")[0])

                scene_type = (line.split(":")[-1]).strip()
                compress_down_scenes.append((first_num, second_num, scene_type))

    compress_copy = []
    i = 0
    detected_ads = 0
    while i < len(compress_down_scenes):
        if i < len(compress_down_scenes) - 1 and compress_down_scenes[i][2] == "ad" and compress_down_scenes[i+1][2] == "ad":
            new_i = i
            while new_i < len(compress_down_scenes) and compress_down_scenes[new_i][2] == "ad":
                new_i += 1
            frames_in_ad = compress_down_scenes[new_i - 1][1] - compress_down_scenes[i][0]
            first_ad_short = (frames_in_ad < 415 and i == 0 and compress_down_scenes[i][2] == "ad" and compress_down_scenes[i+1][2] == "scene")
            
            if frames_in_ad < 390 or first_ad_short:
                new_compress = (compress_down_scenes[i][0], compress_down_scenes[new_i - 1][1], "scene")
            elif frames_in_ad > 1000:
                new_compress = (compress_down_scenes[i][0], compress_down_scenes[i][1], "scene")
                compress_copy.append(new_compress)
                new_compress = (compress_down_scenes[i+1][0], compress_down_scenes[new_i - 1][1], "ad")
            else:
                new_compress = (compress_down_scenes[i][0], compress_down_scenes[new_i - 1][1], "ad")
            compress_copy.append(new_compress)
            detected_ads += 1
            i = new_i
        else:
            frames_in_ad = compress_down_scenes[i][1] - compress_down_scenes[i][0]
            
            first_ad_short = (frames_in_ad < 415 and i == 0 and compress_down_scenes[i][2] == "ad" and compress_down_scenes[i+1][2] == "scene")
            too_many_ads = (frames_in_ad < 400 and compress_down_scenes[i][2] == "ad" and detected_ads >= 2)
            too_short = (frames_in_ad < 390 and compress_down_scenes[i][2] == "ad")

            if too_short or too_many_ads or first_ad_short: 
                compress_copy.append((compress_down_scenes[i][0], compress_down_scenes[i][1], "scene"))
            else:
                compress_copy.append(compress_down_scenes[i])
            if compress_down_scenes[i][2] == "ad":
                detected_ads += 1
            i += 1
    compress_copy = [str(x[0]) + "-" + str(x[1]) + ": " + x[2] + "\n" for x in compress_copy]
    with open(output_file, 'w') as f:
        f.writelines(compress_copy)
    with open(secondary_cached_output, 'w') as f:
        f.writelines(compress_copy)
    return True