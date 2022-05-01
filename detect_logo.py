import numpy as np
import cv2
import sys 
import os
import io
import matplotlib
import matplotlib.pyplot as plt
from os.path import exists

WIDTH = 480
HEIGHT = 270
num = "1"
BASE = "dataset-00" + num + "-00" + num + "/dataset"
sourcefile = BASE + "/Videos/data_test" + num + ".rgb"
brands = [BASE + "/Brand Images/" + x for x in os.listdir(BASE + "/Brand Images") if ".rgb" in x]
brands = sorted(brands)

NUM_FRAMES = 9000

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

assert len(brands) == 2
brand_1 = get_ad_image(brands[0])
#brand_2 = get_ad_image(brands[1])
brand_2_cropped = cv2.imread("aaa.png")

brand_1_cropped = get_cropped_brand(brand_1)
#brand_2_cropped = get_cropped_brand(brand_2)



def createDetector():
    detector = cv2.ORB_create(nfeatures=2000)
    return detector


def getFeatures(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    detector = createDetector()
    kps, descs = detector.detectAndCompute(gray, None)
    return kps, descs, img.shape[:2][::-1]

train_features = getFeatures(brand_2_cropped)

def detectFeatures(img, train_features):
    img = np.copy(img[0:200, 0:300, :])

    train_kps, train_descs, shape = train_features
    # get features from input image
    kps, descs, _ = getFeatures(img)

    # check if keypoints are extracted
    if not kps:
        return None
    # now we need to find matching keypoints in two sets of descriptors (from sample image, and from current image)
    # knnMatch uses k-nearest neighbors algorithm for that
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(train_descs, descs, k=2)
    good = []
    # apply ratio test to matches of each keypoint
    # idea is if train KP have a matching KP on image, it will be much closer than next closest non-matching KP,
    # otherwise, all KPs will be almost equally far
    for m, n in matches:
        if m.distance < 0.8 * n.distance:
            good.append([m])
    
    img3 = cv2.drawMatchesKnn(np.copy(brand_2_cropped),train_kps,img,kps,good,None,flags=2)
    cv2.imwrite("brand2.png", img3)
    sys.exit(0)

    try:
        

        # stop if we didn't find enough matching keypoints
        if len(good) < 0.1 * len(train_kps):
            print(len(good))
            
            return None
        sys.exit(0)
        # estimate a transformation matrix which maps keypoints from train image coordinates to sample image
        src_pts = np.float32([train_kps[m[0].queryIdx].pt for m in good
                              ]).reshape(-1, 1, 2)
        dst_pts = np.float32([kps[m[0].trainIdx].pt for m in good
                              ]).reshape(-1, 1, 2)

        m, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        if m is not None:
            # apply perspective transform to train image corners to get a bounding box coordinates on a sample image
            scene_points = cv2.perspectiveTransform(np.float32([(0, 0), (0, shape[0] - 1),
                                                                (shape[1] - 1, shape[0] - 1),
                                                                (shape[1] - 1, 0)]).reshape(-1, 1, 2), m)
            rect = cv2.minAreaRect(scene_points)
            # check resulting rect ratio knowing we have almost square train image
            #if rect[1][1] > 0 and 0.8 < (rect[1][0] / rect[1][1]) < 1.2:
            return rect
    except:
        pass
    return None

def create_hue_hist(image):
    BINS = 16
    NORM_IMAGE_PIXELS = 1000
    
    h, w = image.shape
    current_pixels = h * w
    rgbhist = np.zeros([BINS+1], np.float32)
    bsize = 256 / BINS
    hues = image // bsize

    for val in np.unique(hues):
        count = np.count_nonzero(hues == val)
        rgbhist[int(val)] = int((count / current_pixels) * NORM_IMAGE_PIXELS)
    
    return rgbhist

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




brand_1_hue = cv2.cvtColor(brand_1_cropped, cv2.COLOR_RGB2HSV)[:, :, 0]
brand_2_hue = cv2.cvtColor(brand_2_cropped, cv2.COLOR_RGB2HSV)[:, :, 0]


imageresult = cv2.drawKeypoints(brand_2_cropped, train_features[0], None, color=(255,0,0), flags=0)
cv2.imwrite("brand.png", imageresult)

unique_1_colors = np.unique(brand_1_hue)
unique_2_colors = np.unique(brand_2_hue)

hue_1 = create_hue_hist(brand_1_hue)
hue_2 = create_hue_hist(brand_2_hue)

video_file = open(sourcefile, 'rb')
fi  = io.FileIO(video_file.fileno())
fb = io.BufferedReader(fi)
for i in range(0, 1900):
    frame = get_next_frame(fb)
    
for i in range(1900, 2000):
    frame = get_next_frame(fb)
    region = detectFeatures(frame, train_features)
    if region is not None:
        print(i)
        box = cv2.boxPoints(region)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
    cv2.imwrite("temp/detect" + str(i) + ".png", frame)

fb.close()