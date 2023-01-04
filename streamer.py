import base64
import cv2
import asyncio
import odrpc
import time
import logging
from fresh_frame import FreshestFrame

class Streamer:
    def __init__(self, doods):
        self.doods = doods
        self.logger = logging.getLogger("doods.streamer")

    def start_stream(self, detect_request: odrpc.DetectRequest):
        url = detect_request.data

        last_frame_time = 0
        vcap = self.create_vcap(url)
        while True:
            # Handle throttling
            if time.time() - last_frame_time < detect_request.throttle:
                time.sleep(detect_request.throttle - (time.time() - last_frame_time))
            last_frame_time = time.time()

            # Get a frame
            seqnum, detect_request.data = vcap.read()
            if detect_request.data is None:
                self.logger.error("Got no data back from video capture. Assuming stream error and attempting to re-create...")
                vcap.release()
                vcap = self.create_vcap(url)
                continue

            detect_response = self.doods.detect(detect_request)

            stop = yield detect_response
            if stop:
                vcap.release()
                return

    def create_vcap(self, url):
        vcap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        vcap = FreshestFrame(vcap)
        return vcap

    @staticmethod
    async def mjpeg_streamer(gen):
        try:
            for detect_response in gen:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(detect_response.image) + b'\r\n')
                await asyncio.sleep(0.01)
        except StopIteration:
            pass
        except asyncio.CancelledError:
            try: 
                gen.send(True) # Stop
            except StopIteration:
                pass
