#!/usr/bin/python

# Alternate detection script using neural nets and YoloV3. 
# slower than openCV HOG but much more accurate
# also capable of detecting many more objects

# Needs opencv-python-3.4.3.18 or above
# On my non GPU machine, this takes 2 seconds while HOG takes 0.2 seconds

# This trained model is able to detect the following 80 categories
# https://github.com/arunponnusamy/object-detection-opencv/blob/master/yolov3.txt

# core code credit: https://github.com/arunponnusamy/cvlib

import sys
import cv2
import argparse
import datetime
import os
import numpy as np

initialize = True
net = None
classes = None

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--delete", action="store_true",  help="delete image after processing")
ap.add_argument("-i", "--image", required=True, help="image with path")
ap.add_argument("-c", "--config", required=True, help="config file with path")
ap.add_argument("-w", "--weight", required=True, help="weight file with path")
ap.add_argument("-l", "--label", required=True, help="label file with path")
ap.add_argument("-t", "--time", action="store_true", help="print time")
args = vars(ap.parse_args())

def populate_class_labels():

    class_file_abs_path = args["label"];
    f = open(class_file_abs_path, 'r')
    classes = [line.strip() for line in f.readlines()]
    return classes


def get_output_layers(net):
    
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers

def detect_common_objects(image):

    Height, Width = image.shape[:2]
    scale = 0.00392

    global classes

    config_file_abs_path = args["config"]
    weights_file_abs_path = args["weight"]
    
    global initialize
    global net

    if initialize:
        classes = populate_class_labels()
        net = cv2.dnn.readNet(weights_file_abs_path, config_file_abs_path)
        initialize = False

    blob = cv2.dnn.blobFromImage(image, scale, (416,416), (0,0,0), True, crop=False)

    net.setInput(blob)

    outs = net.forward(get_output_layers(net))

    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])


    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    bbox = []
    label = []
    conf = []

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        bbox.append([round(x), round(y), round(x+w), round(y+h)])
        label.append(str(classes[class_ids[i]]))
        conf.append(confidences[i])
        
    return bbox, label, conf

# image
image = cv2.imread(args["image"])

start = datetime.datetime.now()
bbox, label, conf = detect_common_objects(image)

if (args["time"]):
    print("[INFO] detection took: {}s".format((datetime.datetime.now() - start).total_seconds()))

pred=""

seen = {}
for l,c in zip (label,conf):
    if l not in seen:
        pred = pred +l+':{:.0%}'.format(c)+' '
        seen[l] = 1

if pred !="":
    pred = "detected:"+pred
print pred
if (args["delete"]):
    os.remove(args["image"])

