import odrpc
import json
import base64
import logging
import asyncio
import threading
import paho.mqtt.client as mqtt
from streamer import Streamer


class MQTT():
    def __init__(self, config, doods):
        self.config = config
        self.doods = doods
        self.mqtt_client = mqtt.Client()
        # Borrow the uvicorn logger because it's pretty.
        self.logger = logging.getLogger("doods.api")

    async def stream(self, detect_request: str = '{}'):
        streamer = None
        try:
            # Run the stream detector and return the results.
            streamer = Streamer(self.doods).start_stream(detect_request)
            for detect_response in streamer:
                # If we requested an image, base64 encode it back to the user
                if detect_request.image:
                    detect_response.image = base64.b64encode(detect_response.image).decode('utf-8')
                for detection in detect_response.detections:
                    self.mqtt_client.publish(f"doods/detect/{detect_request.id}", payload=json.dumps(detection.asdict()), qos=0, retain=False)

        except Exception as e:
            self.logger.info(e)
            try:
                if streamer:
                    streamer.send(True)  # Stop the streamer
            except StopIteration:
                pass

    def run(self):
        if (self.config.broker.user):
            self.mqtt_client.username_pw_set(self.config.broker.user, self.config.broker.password)
        self.mqtt_client.connect(self.config.broker.url, self.config.broker.port, 60)
        for request in self.config.requests:
            asyncio.run(self.stream(request))
