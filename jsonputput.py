import json
import time
import base64

""" Simple script to show the format of the json data that we will be sending via MQTT to AWS IOT Core
    Loads a test image and outputs json with image base64 encoded
    N.B. AWS IOT Core MQTT limit to 128KB per message  
"""

with open("assets/test1.jpg", "rb") as image_file:
        base64_bytes = base64.b64encode(image_file.read())
        base64_string = base64_bytes.decode('utf-8')

json_results = []
json_results.append({
    'image' : base64_string ,
    'device_id' : "1234567890",
    'frame_count' : 1,
    'timestamp' : time.time() ,
    'latitude' : 53.4212 ,
    'longitude' : -6.1412 ,
    'gps_speed' : 10 ,
    'road_segmentation' :
        {
            'road_detected' : True ,
            'confidence' : 80
        },
    'people_detection' :
        {
            'people_count' : 0
        }
})

json_message = json.dumps(json_results, indent=2)
with open("assets/output.json", 'w') as output_file:
    output_file.write(json_message)