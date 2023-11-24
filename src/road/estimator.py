#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np
import configparser
import time
import threading

# from src.battery.monitor import BatteryMonitor
from src.gps.reader import GPSReader
from src.aws_iot.sender import AWSIoT
from src.sensehat.display import RpiSenseHat
from settings import ROAD_MODEL_PATH, NN_HEIGHT, NN_WIDTH, CONFIG_FILE, CLASSES_COLOR_MAP

'''
Road Segmentation example based on https://github.com/luxonis/depthai-experiments/tree/master/gen2-deeplabv3_person

python3 -m pip install -r requirements.txt
python3 road_segmentation.py

Model road-segmentation-adas-0001 from Open Model Zoo

export OPEN_MODEL_DOWNLOADER=/opt/intel/openvino/deployment_tools/open_model_zoo/tools/downloader/downloader.py
$OPEN_MODEL_DOWNLOADER --name road-segmentation-adas-0001  --output_dir ~/Downloads/Luna/open_model_zoo_downloads/

Convert to Blob for myriad VPU

/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/myriad_compile -ip U8 -VPU_NUMBER_OF_SHAVES 6 
-VPU_NUMBER_OF_CMX_SLICES 6 -m /home/barry/Downloads/Luna/open_model_zoo_downloads/intel/road-segmentation-adas-0001
/FP16/road-segmentation-adas-0001.xml -o models/road-segmentation-adas-0001.blob 

'''


class RoadSegmentater:
    def __init__(self):
        params = configparser.ConfigParser()
        params.read(CONFIG_FILE)
        # self.battery_monitor = BatteryMonitor()
        self.mqtt_sender = AWSIoT()
        self.sensehat = RpiSenseHat()
        self.gps_reader = GPSReader()
        self.cam_source = params.get("ROAD_SEG", "cam_input")
        self.video_output = params.get("ROAD_SEG", "video_output")
        self.full_segmentation = params.get("ROAD_SEG", "full_segmentation")
        self.road_confidence = params.get("ROAD_SEG", "confidence")
        self.non_road_confidence = 1 - float(self.road_confidence)
        self.q_nn_input = None
        self.q_nn = None
        self.box_y1 = 0
        self.box_x1 = 0
        self.box_x2 = 0
        self.box_pixels = 0
        self.video_out = None
        self.road = False
        self.__initialize_model()

    @staticmethod
    def show_segmentation(output_colors, frame):
        return cv2.addWeighted(frame, 1, output_colors, 0.5, 0)

    def __initialize_model(self):
        # only show segmentation output in bounding box
        if self.full_segmentation == "yes":
            self.box_y1 = 0
            self.box_x1 = 0
            self.box_x2 = NN_WIDTH
            self.box_pixels = NN_WIDTH * NN_HEIGHT
        else:
            self.box_y1 = 300
            self.box_x1 = 300
            self.box_x2 = 596
            self.box_pixels = (NN_HEIGHT - self.box_y1) * (self.box_x2 - self.box_x1)

        # Start defining a pipeline
        pipeline = dai.Pipeline()
        pipeline.setOpenVINOVersion(version=dai.OpenVINO.Version.VERSION_2021_2)

        # Define a neural network that will make predictions based on the source frames
        detection_nn = pipeline.createNeuralNetwork()
        detection_nn.setBlobPath(ROAD_MODEL_PATH)
        detection_nn.setNumPoolFrames(4)
        detection_nn.input.setBlocking(False)
        detection_nn.setNumInferenceThreads(2)

        cam = None
        # Define a source - color camera
        if self.cam_source == 'rgb':
            cam = pipeline.createColorCamera()
            cam.setPreviewSize(NN_WIDTH, NN_HEIGHT)
            cam.setInterleaved(False)
            cam.preview.link(detection_nn.input)
        elif self.cam_source == 'left':
            cam = pipeline.createMonoCamera()
            cam.setBoardSocket(dai.CameraBoardSocket.LEFT)
        elif self.cam_source == 'right':
            cam = pipeline.createMonoCamera()
            cam.setBoardSocket(dai.CameraBoardSocket.RIGHT)
        if self.cam_source != 'rgb':
            man_ip = pipeline.createImageManip()
            man_ip.setResize(NN_WIDTH, NN_HEIGHT)
            man_ip.setKeepAspectRatio(True)
            man_ip.setFrameType(dai.RawImgFrame.Type.BGR888p)
            cam.out.link(man_ip.inputImage)
            man_ip.out.link(detection_nn.input)
        cam.setFps(20)

        # Create outputs
        x_out_rgb = pipeline.createXLinkOut()
        x_out_rgb.setStreamName("nn_input")
        x_out_rgb.input.setBlocking(False)
        detection_nn.passthrough.link(x_out_rgb.input)

        x_out_nn = pipeline.createXLinkOut()
        x_out_nn.setStreamName("nn")
        x_out_nn.input.setBlocking(False)
        detection_nn.out.link(x_out_nn.input)

        # Pipeline defined, now the device is assigned and pipeline is started
        self.device = dai.Device(pipeline)
        self.device.startPipeline()

        # Output queues will be used to get the rgb frames and nn data from the outputs defined above
        self.q_nn_input = self.device.getOutputQueue(name="nn_input", maxSize=10, blocking=False)
        self.q_nn = self.device.getOutputQueue(name="nn", maxSize=10, blocking=False)

        return

    def run(self):
        # battery_threading = threading.Thread(target=self.battery_monitor.run)
        # battery_threading.start()
        video_time = time.time()
        if self.video_output == "yes":
            # Output Video
            self.video_out = cv2.VideoWriter('output_' + str(video_time) + '.avi',
                                             cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 2, (NN_WIDTH, NN_HEIGHT))

        start_time = time.time()
        frame_count = 0
        counter = 0
        fps = 0
        layer_info_printed = False
        layer_dims = []
        while True:
            # instead of get (blocking) used tryGet (non_blocking) which will return the available data or None
            # otherwise
            in_nn_input = self.q_nn_input.get()
            in_nn = self.q_nn.get()

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
                            layer_dims = layer.dims[::-1]  # reverse dimensions
                            print(f"dims: {layer_dims}")
                        layer_info_printed = True
                    # get layer1 data
                    layer1 = in_nn.getFirstLayerFp16()
                    # reshape to numpy array
                    layer1 = np.asarray(layer1, dtype=np.float).reshape(layer_dims)
                    classes_map = np.zeros(shape=(NN_HEIGHT, NN_WIDTH, 3), dtype=np.uint8)
                    road_pixels = 0
                    non_road_pixels = 0
                    for i in range(self.box_y1, NN_HEIGHT):
                        for j in range(self.box_x1, self.box_x2):
                            if len(layer1[0, :, i, j]) == 1:
                                pixel_class = int(layer1[0, :, i, j])
                            else:
                                pixel_class = np.argmax(layer1[0, :, i, j])
                            classes_map[i, j, :] = CLASSES_COLOR_MAP[min(pixel_class, 20)]
                            # count road pixels
                            if pixel_class == 1:
                                road_pixels += 1
                            else:
                                non_road_pixels += 1

                    if frame is not None:
                        self.road = True
                        if (non_road_pixels / self.box_pixels) > self.non_road_confidence:
                            self.road = False

                        frame = self.show_segmentation(classes_map, frame)
                        cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4),
                                    cv2.FONT_HERSHEY_TRIPLEX, 0.4, (255, 0, 0))
                        cv2.imshow("Road Detector", frame)
                        if self.video_output == "yes":
                            # Write the frame into the file 'output.avi'
                            self.video_out.write(frame)
            if not self.road:
                self.sensehat.display_status(status="sidewalk")
                lat, lon = self.gps_reader.get_gps_position()
                # lat = ""
                # lon = ""
                mqtt_sender_thread = threading.Thread(target=self.mqtt_sender.run,
                                                      args=["", time.time(), lat, lon, self.road, self.road_confidence,
                                                            "", "", "", "", "", ""])
                mqtt_sender_thread.start()
            else:
                self.sensehat.display_status(status="road")

            counter += 1
            frame_count += 1
            if (time.time() - start_time) > 1:
                fps = counter / (time.time() - start_time)
                print(f"fps: {fps}")
                counter = 0
                start_time = time.time()

            if cv2.waitKey(1) == ord('q'):
                break

        if self.video_output == "yes":
            self.video_out.release()

        cv2.destroyAllWindows()


if __name__ == '__main__':
    RoadSegmentater().run()
