
compress_down_scenes = []
num = '2'
with open("data" + num + ".txt", 'r') as f:
    lines  = f.readlines()
    for line in lines:
        if "," not in line:
            first_num = int(line.split("-")[0])
            second_num = int(line.split("-")[-1].split(":")[0])

            scene_type = (line.split(":")[-1]).strip()
            compress_down_scenes.append((first_num, second_num, scene_type))

compress_copy = [compress_down_scenes[0],]
i = 1
detected_ads = 0
while i < len(compress_down_scenes):
    if i < len(compress_down_scenes) - 1 and compress_down_scenes[i][2] == "ad" and compress_down_scenes[i+1][2] == "ad":
        new_i = i
        while new_i < len(compress_down_scenes) and compress_down_scenes[new_i][2] == "ad":
            new_i += 1
        frames_in_ad = compress_down_scenes[new_i - 1][1] - compress_down_scenes[i][0]
        if frames_in_ad < 390:
            new_compress = (compress_down_scenes[i][0], compress_down_scenes[new_i - 1][1], "scene")
        else:
            new_compress = (compress_down_scenes[i][0], compress_down_scenes[new_i - 1][1], "ad")
        compress_copy.append(new_compress)
        detected_ads += 1
        i = new_i
    else:
        frames_in_ad = compress_down_scenes[i][1] - compress_down_scenes[i][0]
        
        if (frames_in_ad < 390 and compress_down_scenes[i][2] == "ad") or (frames_in_ad < 400 and compress_down_scenes[i][2] == "ad" and detected_ads >= 2): 
            compress_copy.append((compress_down_scenes[i][0], compress_down_scenes[i][1], "scene"))
        else:
            compress_copy.append(compress_down_scenes[i])
        if compress_down_scenes[i][2] == "ad":
            detected_ads += 1
        i += 1
compress_copy = [str(x[0]) + "-" + str(x[1]) + ": " + x[2] + "\n" for x in compress_copy]
with open("data-edited" + num + ".txt", 'w') as f:
    f.writelines(compress_copy)