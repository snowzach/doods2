import base64
import cv2
import asyncio
import odrpc
from fastapi.responses import StreamingResponse
from fresh_frame import FreshestFrame

class Streamer:
    def __init__(self, doods):
        self.doods = doods

    def start_stream(self, url, detect_request: odrpc.DetectRequest):
        vcap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        vcap = FreshestFrame(vcap)
        while True:
            ret, frame = vcap.read()
            if ret == False:
                continue
            else:
                (flag, encodedImage) = cv2.imencode(".jpg", frame)
                if not flag:
                    continue
                detect_request.data = base64.b64encode(encodedImage)
                image = self.doods.detect(detect_request, True)
            stop = yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(image) + b'\r\n')
            if stop:
                vcap.release()
                return

    @staticmethod
    async def streamer(gen):
        try:
            for i in gen:
                yield i
                await asyncio.sleep(0.01)
        except StopIteration:
            pass
        except asyncio.CancelledError:
            try: 
                gen.send(True) # Stop
            except StopIteration:
                pass

    def stream_response(self, url, detect_request):
        return StreamingResponse(Streamer.streamer(self.start_stream(url, detect_request)), media_type="multipart/x-mixed-replace;boundary=frame")

