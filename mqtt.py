import uvicorn
import json
import base64
import logging
import threading
import time
import cv2
import paho.mqtt.client as mqtt
import numpy as np
from streamer import Streamer
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

class MQTT():
    def __init__(self, config, doods, metrics_server_config=None):
        self.config = config
        self.doods = doods
        self.metrics_server_config = metrics_server_config
        self.mqtt_client = mqtt.Client()
        # Borrow the uvicorn logger because it's pretty.
        self.logger = logging.getLogger("doods.mqtt")

    def stream(self, mqtt_detect_request: str = '{}'):
        streamer = None
        try:
            # Run the stream detector and return the results.
            streamer = Streamer(self.doods).start_stream(mqtt_detect_request)
            for detect_response in streamer:
                # If separate_detections, iterate over each detection and process it separately
                if mqtt_detect_request.separate_detections:

                    #If we're going to be cropping, do this processing only once (rather than for each detection)
                    if mqtt_detect_request.image and mqtt_detect_request.crop:
                        detect_image_bytes = np.frombuffer(detect_response.image, dtype=np.uint8)
                        detect_image = cv2.imdecode(detect_image_bytes, cv2.IMREAD_COLOR)
                        di_height, di_width = detect_image.shape[:2]


                    for detection in detect_response.detections:
                        # If an image was requested
                        if mqtt_detect_request.image:
                            # Crop image to detection box if requested
                            if mqtt_detect_request.crop:
                                cropped_image = detect_image[
                                int(detection.top*di_height):int(detection.bottom*di_height), 
                                int(detection.left*di_width):int(detection.right*di_width)]
                                mqtt_image = cv2.imencode(mqtt_detect_request.image, cropped_image)[1].tostring()
                            else:
                                mqtt_image = detect_response.image


                            # For binary images, publish the image to its own topic
                            if mqtt_detect_request.binary_images:
                                self.mqtt_client.publish(
                                    f"doods/image/{mqtt_detect_request.id}{'' if detection.region_id is None else '/'+detection.region_id}/{detection.label or 'object'}", 
                                    payload=mqtt_image, qos=0, retain=False)
                            # Otherwise add base64-encoded image to the detection
                            else:
                                detection.image = base64.b64encode(mqtt_image).decode('utf-8')

                        self.mqtt_client.publish(
                            f"doods/detect/{mqtt_detect_request.id}{'' if detection.region_id is None else '/'+detection.region_id}/{detection.label or 'object'}", 
                            payload=json.dumps(detection.asdict(include_none=False)), qos=0, retain=False)
                
                # Otherwise, publish the collected detections together
                else:
                    # If an image was requested
                    if mqtt_detect_request.image:
                        # If binary_images, move the image from the response and publish it to a separate topic
                        if mqtt_detect_request.binary_images:
                            mqtt_image = detect_response.image
                            detect_response.image = None
                            self.mqtt_client.publish(
                                f"doods/image/{mqtt_detect_request.id}", 
                                payload=detect_response.image, qos=0, retain=False)
                        # Otherwise, inlcude the base64-encoded image in the response
                        else:
                            detect_response.image = base64.b64encode(detect_response.image).decode('utf-8')
                    
                    self.mqtt_client.publish(
                            f"doods/detect/{mqtt_detect_request.id}", 
                            payload=json.dumps(detect_response.asdict(include_none=False)), qos=0, retain=False)
                    

        except Exception as e:
            self.logger.info(e)
            try:
                if streamer:
                    streamer.send(True)  # Stop the streamer
            except StopIteration:
                pass

    def metrics_server(self, config):
        app = FastAPI()
        self.instrumentator = Instrumentator(
            excluded_handlers=["/metrics"],
        )
        self.instrumentator.instrument(app).expose(app)
        uvicorn.run(app, host=config.host, port=config.port, log_config=None)

    def run(self):
        if (self.config.broker.user):
            self.mqtt_client.username_pw_set(self.config.broker.user, self.config.broker.password)
        self.mqtt_client.connect(self.config.broker.host, self.config.broker.port, 60)

        for request in self.config.requests:
            threading.Thread(target=self.stream, args=(request,)).start()

        if self.config.metrics:
            self.logger.info("starting metrics server")
            self.metrics_server(self.metrics_server_config)


