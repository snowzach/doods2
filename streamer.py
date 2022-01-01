import base64
import cv2
import asyncio
import odrpc
import time
from fresh_frame import FreshestFrame

class Streamer:
    def __init__(self, doods):
        self.doods = doods

    def start_stream(self, detect_request: odrpc.DetectRequest):
        vcap = cv2.VideoCapture(detect_request.data, cv2.CAP_FFMPEG)
        vcap = FreshestFrame(vcap)
        last_frame_time = 0
        while True:
            # Handle throttling
            if time.time() - last_frame_time < detect_request.throttle:
                time.sleep(detect_request.throttle - (time.time() - last_frame_time))
            last_frame_time = time.time()
    
            # Get a frame
            ret, detect_request.data = vcap.read()
            if ret == False:
                continue
            detect_response = self.doods.detect(detect_request)
            
            stop = yield detect_response
            if stop:
                vcap.release()
                return

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
