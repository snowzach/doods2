import uvicorn
import doods
import odrpc
import json
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from typing import List
from streamer import Streamer

# Initialize DOODS
d = doods.Doods()

app = FastAPI()

@app.get("/detectors", response_model=List[odrpc.Detector], response_model_exclude_none=True)
async def detectors():
    return d.detectors()

@app.post("/detect", response_model=odrpc.DetectResponse, response_model_exclude_none=True)
async def detect(detect_request: odrpc.DetectRequest):
    return d.detect(detect_request)

@app.post("/image")
async def image(detect_request: odrpc.DetectRequest):
    image = d.detect(detect_request, True)
    return Response(content=image, media_type="image/png")

@app.get("/stream")
async def stream(url: str, detect_config: str = '{}'):
    detect_config_dict = json.loads(detect_config)
    detect_request = odrpc.DetectRequest(**detect_config_dict)
    print(detect_request)
    return Streamer(d).stream_response(url, detect_request)

# Mount the static directory
app.mount("/", StaticFiles(directory="html", html=True), name="static")

# Start uvicorn app
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080, access_log=True)
