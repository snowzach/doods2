import uvicorn
import doods
import odrpc
import json
import base64
import logging
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from streamer import Streamer

# Initialize DOODS
d = doods.Doods()
app = FastAPI()

# Borrow the uvicorn logger because it's pretty.
logger = logging.getLogger("uvicorn.doods")

@app.get("/detectors", response_model=List[odrpc.Detector], response_model_exclude_none=True)
async def detectors():
    return d.detectors()

@app.post("/detect", response_model=odrpc.DetectResponse, response_model_exclude_none=True)
async def detect(detect_request: odrpc.DetectRequest):
    # logger.info('detect request: %s', detect_request)
    detect_response = d.detect(detect_request)
    # If we requested an image, base64 encode it back to the user
    if detect_request.image:
        detect_response.image = base64.b64encode(detect_response.image)
    return detect_response

@app.post("/image")
async def image(detect_request: odrpc.DetectRequest):
    # logger.info('image request: %s', detect_request)
    if not detect_request.image:
        detect_request.image = ".jpg"
    detect_response = d.detect(detect_request)
    return Response(content=detect_response.image, media_type="image/jpeg")

@app.get("/stream")
async def stream(detect_config: str = '{}'):
    detect_config_dict = json.loads(detect_config)
    detect_request = odrpc.DetectRequest(**detect_config_dict)
    # logger.info('stream request: %s', detect_request)
    detect_request.image = ".jpg" # Must be jpg
    return StreamingResponse(Streamer.mjpeg_streamer(Streamer(d).start_stream(detect_request)), media_type="multipart/x-mixed-replace;boundary=frame")

@app.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    streamer = None
    try:
        # Fetch the initial request payload
        detect_config = await websocket.receive_json()
        detect_request = odrpc.DetectRequest(**detect_config)

        # Run the stream detector and return the results.
        streamer = Streamer(d).start_stream(detect_request)
        for detect_response in streamer:
            # If we requested an image, base64 encode it back to the user
            if detect_request.image:
                detect_response.image = base64.b64encode(detect_response.image).decode('utf-8')
            await websocket.send_json(detect_response.asdict(include_none=False))            
            # Fake poll to maintain updated connection state
            try:
                await asyncio.wait_for(websocket.receive_text(), 0.0001)   
            except asyncio.TimeoutError:
                pass

    except Exception as e:
        logger.info(e)
        try:
            if streamer:
                streamer.send(True) # Stop the streamer
        except StopIteration:
            pass

# Mount the UI directory
app.mount("/", StaticFiles(directory="html", html=True), name="static")

# Start uvicorn app
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080, access_log=True)
