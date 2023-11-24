"""
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 """

import logging
import time
import json
import configparser

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from settings import ALLOWED_ACTIONS, CONFIG_FILE


# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class AWSIoT:
    def __init__(self):
        params = configparser.ConfigParser()
        params.read(CONFIG_FILE)
        self.host = params.get("AWS_IOT", "host")
        self.root_ca_path = params.get("AWS_IOT", "root_CA_path")
        self.certificate_path = params.get("AWS_IOT", "certificate_path")
        self.private_key_path = params.get("AWS_IOT", "private_key_path")
        self.port = int(params.get("AWS_IOT", "port"))
        self.use_websocket = params.get("AWS_IOT", "use_websocket")
        self.clientId = params.get("AWS_IOT", "client_id")
        self.topic = params.get("AWS_IOT", "topic")
        self.mode = params.get("AWS_IOT", "mode")
        self.message = params.get("AWS_IOT", "message")
        self.run_ret = True
        self.mqtt_client = None
        self.__initialize()

    # Custom MQTT message callback
    @staticmethod
    def custom_callback(client, userdata, message):
        print("[INFO] Received a new message: ")
        print(message.payload)
        print("[INFO] from topic: ")
        print(message.topic)
        print("--------------\n\n")

    def __initialize(self):
        if self.mode not in ALLOWED_ACTIONS:
            self.run_ret = False
            print(f"[INFO] Unknown --mode option {self.mode}. Must be one of {ALLOWED_ACTIONS}")
            return

        if self.use_websocket.lower() == "true" and self.certificate_path != "" and self.private_key_path != "":
            self.run_ret = False
            print("[INFO] X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
            return

        if self.use_websocket.lower() == "false" and (self.certificate_path == "" or self.private_key_path == ""):
            self.run_ret = False
            print("[INFO] Missing credentials for authentication.")
            return

        # Port defaults
        # When no port override for WebSocket, default to 443
        if self.use_websocket.lower() == "true" and self.port == "":
            self.port = 443
        # When no port override for non-WebSocket, default to 8883
        if self.use_websocket.lower() == "false" and self.port == "":
            self.port = 8883

        # Init AWSIoTMQTTClient
        if self.use_websocket.lower() == "true":
            self.mqtt_client = AWSIoTMQTTClient(self.clientId, useWebsocket=True)
            self.mqtt_client.configureEndpoint(self.host, self.port)
            self.mqtt_client.configureCredentials(self.root_ca_path)
        else:
            self.mqtt_client = AWSIoTMQTTClient(self.clientId)
            self.mqtt_client.configureEndpoint(self.host, self.port)
            self.mqtt_client.configureCredentials(self.root_ca_path, self.private_key_path, self.certificate_path)

        # AWSIoTMQTTClient connection configuration
        self.mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
        self.mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
        self.mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect and subscribe to AWS IoT
        self.mqtt_client.connect()
        if self.mode == 'both' or self.mode == 'subscribe':
            self.mqtt_client.subscribe(self.topic, 1, self.custom_callback)
        time.sleep(2)

        return

    def run(self, device_id, time_stamp, lat, lon, road_ret, road_confidence, people_count,
            people_confidence, xmin, xmax, ymin, ymax):
        # Publish to the same topic in a loop forever
        loop_count = 0
        while True:
            if not self.run_ret:
                break
            if self.mode == 'both' or self.mode == 'publish':
                message = {
                    "device_id": device_id,
                    "timestamp": time_stamp,
                    "latitude": lat,
                    "longitude": lon,
                    "road_segmentation": {
                        "road_detected": road_ret,
                        "confidence": road_confidence
                    },
                    "people_detection": {
                        "people_count": people_count,
                        "bounding_box": [
                            {
                                "confidence": people_confidence,
                                "xmin": xmin,
                                "ymin": ymin,
                                "xmax": xmax,
                                "ymax": ymax,
                            }
                        ]
                    },
                    "message": self.message,
                    "sequence": loop_count
                }
                message_json = json.dumps(message)
                self.mqtt_client.publish(self.topic, message_json, 1)
                if self.mode == 'publish':
                    print(f'[INFO] Published topic {self.topic}: {message_json}\n')
                loop_count += 1
            time.sleep(1)

        return


if __name__ == '__main__':
    AWSIoT().run(device_id="1234567890", time_stamp=1618842457.3578696, lat=53.42, lon=6.14, road_ret=False,
                 road_confidence=0.0, people_count=0, people_confidence=91, xmin=100, ymin=100, xmax=200, ymax=200)
