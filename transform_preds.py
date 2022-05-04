import json
import os
import sys

video_to_hash = {
    1: "7f91457d3f5cc71141579e0afbe9a053",
    2: "1df718b7af04bd0fe044e35faf758aa1",
    3: "ff50d22b76b36cbb5ec0226069d26ad2",
    4: "0ab729e54aba8269827629f32b006c87",
}

INPUT_FOLDER = "preds/"
OUTPUT_FOLDER = "preds_transformed/"

if not os.path.exists(OUTPUT_FOLDER):
    os.mkdir(OUTPUT_FOLDER)


for f in [x for x in os.listdir(INPUT_FOLDER)]:
    new_lines = []
    with open(INPUT_FOLDER + f, 'r') as fl:
        lines = fl.readlines()
        for raw_line in lines:
            for num in range(1, 5):
                if "video-" + str(num) in raw_line:
                    line = raw_line.replace("video-" + str(num), "video-" + video_to_hash[num])
                    new_lines.append(line)
                    break
    
    with open(OUTPUT_FOLDER + f, 'w') as fl:
        fl.writelines(new_lines)
