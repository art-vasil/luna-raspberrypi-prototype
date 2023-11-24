#!/usr/bin/env python3

from pathlib import Path
import cv2
import depthai as dai
import numpy as np
import argparse
import time
import sys

'''
Road Segmentaion example based on https://github.com/luxonis/depthai-experiments/tree/master/gen2-deeplabv3_person

python3 -m pip install -r requirements.txt
python3 road_segmentation.py

Model road-segmentation-adas-0001 from Open Model Zoo

export OPEN_MODEL_DOWNLOADER=/opt/intel/openvino/deployment_tools/open_model_zoo/tools/downloader/downloader.py
$OPEN_MODEL_DOWNLOADER --name road-segmentation-adas-0001  --output_dir ~/Downloads/Luna/open_model_zoo_downloads/

Convert to Blob for myriad VPU

/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/myriad_compile -ip U8 -VPU_NUMBER_OF_SHAVES 6 -VPU_NUMBER_OF_CMX_SLICES 6 -m /home/barry/Downloads/Luna/open_model_zoo_downloads/intel/road-segmentation-adas-0001/FP16/road-segmentation-adas-0001.xml -o models/road-segmentation-adas-0001.blob

'''

cam_options = ['rgb', 'left', 'right']

parser = argparse.ArgumentParser()
parser.add_argument("-cam", "--cam_input", help="select camera input source for inference", default='rgb', choices=cam_options)
parser.add_argument("-video", "--video_output", help="do you want to save a video of output", default='no')
parser.add_argument("-full", "--full_segmentation", help="putput the full segmentmented images", default='yes')
parser.add_argument("-conf", "--confidence", help="confidence needed to infer images as road", default='0.8' , type=float)
parser.add_argument("-nn", "--nn_model", help="select camera input source for inference", default='models/road-segmentation-adas-0001.blob', type=str)

args = parser.parse_args()

cam_source = args.cam_input 
nn_path = args.nn_model
video_output = args.video_output 
full_segmentation = args.full_segmentation
road_confidence = args.confidence
non_road_confidence = 1 - args.confidence 

nn_width = 896
nn_height = 512

#only show segmentation output in bounding box
if full_segmentation == "yes":
    box_y1 = 0
    box_x1 = 0
    box_x2 = nn_width
    box_pixels = nn_width * nn_height
else:
    box_y1 = 300
    box_x1 = 300
    box_x2 = 596
    box_pixels = (nn_height - box_y1) * (box_x2 -box_x1)

classes_color_map = [
    (0, 0, 0), # sky
    (58, 169, 55), # road
    (211, 51, 17),
    (157, 80, 44)
]

def show_segmentation(output_colors, frame):
    return cv2.addWeighted(frame,1, output_colors,0.5,0)

# Start defining a pipeline
pipeline = dai.Pipeline()

pipeline.setOpenVINOVersion(version = dai.OpenVINO.Version.VERSION_2021_2)

# Define a neural network that will make predictions based on the source frames
detection_nn = pipeline.createNeuralNetwork()
detection_nn.setBlobPath(nn_path)

detection_nn.setNumPoolFrames(4)
detection_nn.input.setBlocking(False)
detection_nn.setNumInferenceThreads(2)

cam=None
# Define a source - color camera
if cam_source == 'rgb':
    cam = pipeline.createColorCamera()
    cam.setPreviewSize(nn_width,nn_height)
    cam.setInterleaved(False)
    cam.preview.link(detection_nn.input)
elif cam_source == 'left':
    cam = pipeline.createMonoCamera()
    cam.setBoardSocket(dai.CameraBoardSocket.LEFT)
elif cam_source == 'right':
    cam = pipeline.createMonoCamera()
    cam.setBoardSocket(dai.CameraBoardSocket.RIGHT)

if cam_source != 'rgb':
    manip = pipeline.createImageManip()
    manip.setResize(nn_width,nn_height)
    manip.setKeepAspectRatio(True)
    manip.setFrameType(dai.RawImgFrame.Type.BGR888p)
    cam.out.link(manip.inputImage)
    manip.out.link(detection_nn.input)

cam.setFps(20)

# Create outputs
xout_rgb = pipeline.createXLinkOut()
xout_rgb.setStreamName("nn_input")
xout_rgb.input.setBlocking(False)

detection_nn.passthrough.link(xout_rgb.input)

xout_nn = pipeline.createXLinkOut()
xout_nn.setStreamName("nn")
xout_nn.input.setBlocking(False)

detection_nn.out.link(xout_nn.input)

# Pipeline defined, now the device is assigned and pipeline is started
device = dai.Device(pipeline)
device.startPipeline()

# Output queues will be used to get the rgb frames and nn data from the outputs defined above
q_nn_input = device.getOutputQueue(name="nn_input", maxSize=10, blocking=False)
q_nn = device.getOutputQueue(name="nn", maxSize=10, blocking=False)

video_time = time.time()

if video_output == "yes":
    # Output Video
    vout = cv2.VideoWriter('output_' + str(video_time) + '.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 2, (nn_width,nn_height))

start_time = time.time()
frame_count = 0
counter = 0
fps = 0
layer_info_printed = False
road_segmentation_results = []
while True:
    # instead of get (blocking) used tryGet (nonblocking) which will return the available data or None otherwise
    in_nn_input = q_nn_input.get()
    in_nn = q_nn.get()

    if in_nn_input is not None:
        # if the data from the rgb camera is available, transform the 1D data into a HxWxC frame
        shape = (3, in_nn_input.getHeight(), in_nn_input.getWidth())
        frame = in_nn_input.getData().reshape(shape).transpose(1, 2, 0).astype(np.uint8)
        frame = np.ascontiguousarray(frame)

    if in_nn is not None:
        # print("NN received")
        layers = in_nn.getAllLayers()

        if not layer_info_printed:
            for layer_nr, layer in enumerate(layers):
                print(f"Layer {layer_nr}")
                print(f"Name: {layer.name}")
                print(f"Order: {layer.order}")
                print(f"dataType: {layer.dataType}")
                dims = layer.dims[::-1] # reverse dimensions
                print(f"dims: {dims}")
            layer_info_printed = True

        # get layer1 data
        layer1 = in_nn.getFirstLayerFp16()
        # reshape to numpy array
        layer1 = np.asarray(layer1, dtype=np.float).reshape(dims)
        classes_map = np.zeros(shape=(nn_height, nn_width, 3), dtype=np.uint8)
        road_pixels = 0
        non_road_pixels = 0
        done = 0 
        for i in range(box_y1 , nn_height):
            for j in range(box_x1 , box_x2):
                if len(layer1[0,:, i, j]) == 1:
                    pixel_class = int(layer1[0,:, i, j])
                else:
                    pixel_class = np.argmax(layer1[0,:, i, j])
                classes_map[i, j, :] = classes_color_map[min(pixel_class, 20)]

                #count road pixels
                if pixel_class == 1 :
                    road_pixels+=1
                else :
                    non_road_pixels+=1
               
        if frame is not None:
            road = True
            if ( non_road_pixels / box_pixels ) > non_road_confidence :
                road = False
            
            frame = show_segmentation(classes_map, frame)
            cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, (255, 0, 0))
            cv2.imshow("nn_input", frame)
            if video_output == "yes":
                # Write the frame into the file 'output.avi'
                vout.write(frame)
    
    counter+=1
    frame_count+=1
    if (time.time() - start_time) > 1 :
        fps = counter / (time.time() - start_time)
        print(f"fps: {fps}")
        counter = 0
        start_time = time.time()


    if cv2.waitKey(1) == ord('q'):
        break

if video_output == "yes":
    vout.release()

cv2.destroyAllWindows()