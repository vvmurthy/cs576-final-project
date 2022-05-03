import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import io

WIDTH = 480
HEIGHT = 270

def get_logo_img(logopath):
    imageFile = open(logopath, 'rb')
    fileIO  = io.FileIO(imageFile.fileno())
    fileBuffer = io.BufferedReader(fileIO)
    r_frame = fileBuffer.read(WIDTH * HEIGHT)
    g_frame = fileBuffer.read(WIDTH * HEIGHT)
    b_frame = fileBuffer.read(WIDTH * HEIGHT)
    r_a = np.frombuffer(r_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 
    g_a = np.frombuffer(g_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 
    b_a = np.frombuffer(b_frame, dtype=np.uint8).reshape(HEIGHT, WIDTH) 

    full_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    full_frame[:, :, 0] = r_a
    full_frame[:, :, 1] = g_a
    full_frame[:, :, 2] = b_a
    return full_frame


def detectImg(frame, logos, i):

    maxCount = 0
    maxName = ""
    maxFrame = frame

    for logoname in logos:

        logo = get_logo_img(logos[logoname])
        # logo = cv.imread(logo)

        MIN_MATCH_COUNT = 10
        # Initiate SIFT detector
        sift = cv.SIFT_create()
        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(frame,None)
        kp2, des2 = sift.detectAndCompute(logo,None)
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 100)
        flann = cv.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1,des2,k=2)
        # store all the good matches as per Lowe's ratio test.
        good = []
        for m,n in matches:
            if m.distance < 0.9*n.distance:
                good.append(m)

        # good = good[:10]


        if len(good)>MIN_MATCH_COUNT:
            #edit frame
            src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
            dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
            M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
            matchesMask = mask.ravel().tolist()
            h,w,c = frame.shape
            pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
            dst = cv.perspectiveTransform(pts ,M)
            img2 = cv.polylines(logo,[np.int32(dst)],True,255,3, cv.LINE_AA)

            if len(good) > maxCount:
                maxCount = len(good)
                maxName = logoname
                maxFrame = img2
        else:
            # print( "Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT) )
            matchesMask = None
    
    return maxName, maxFrame
