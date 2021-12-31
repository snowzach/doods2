# DOODS2 - Return of the DOOD
Dedicated Open Object Detection Service - Yes, it's a backronym...

DOODS is a REST service that detects objects in images or video streams. It's designed to be very easy to use, run as a container and available remotely.
It also supports GPUs and EdgeTPU hardware acceleration.

DOODS2 is a rewrite of [DOODS](https://github.com/snowzach/doods) in Python.

Why Python you may ask... Well, lots of machine learning stuff is in Python and there is pretty good support for
Object Detection and helpers in Python. Maintaining the code in Go was basically impossible. 

DOODS2 is designed to have a compatible API specification with DOODS as well as adding some additional features. 
It's my hope that in Python I might get a little more interest from the community in maintaining it and adding features.

DOODS2 drops support for gRPC as I doubt very much anyone used it anyways.

# Quickstart in Docker
On your local machine run: `docker run -it -p 8080:8080 snowzach/doods2:latest` and open a browser to http://localhost:8080 
Try uploading an image file or passing it an RTSP video stream. You can make changes to the specification by referencing the [Detect Request](#detect-request) payload.

Two detectors are included with the base image that you can try.
- default - coco_ssd_mobilenet_v1_1.0_quant.tflite - A decent and fast Tensorflow light object detector.
- tensorflow - faster_rcnn_inception_v2_coco_2018_01_28.pb - A much slower but more accurate object detector.

# REST API
The REST API has several endpoints for detecting objects in images as well as streams. Details of the payloads and endpoints are below.

## DETECT REQUEST
Every request to DOODS involves the detect request JSON object that looks like this.
```json
{
  # This ID field is user definable and will return the same ID that was passed in.
  "id": "whatever",
  # This is the name of the detecor to be used for this detection. If not specified, 'default' will be used.
  "detector_name": "default",
  # Data is either base64 encoded image date for a single image, it may also be a URL to an image
  # For video it's expected to be a URL that can be read by ffmpeg. "rtsp://......" is typical
  "data": "b64 or url",
  # The image option determines, for API calls that return an image, what format the image should be.
  # Supported options currently are "jpeg" and "png"
  "image": "jpeg",
  # The throtle option determines, for streaming API calls only, how often it should return results.
  # in seconds. For example, 5 means return 1 result about every 5 seconds. A value of 0 indicates
  # it should return results as fast as it can. 
  "throttle": 5,
  # Ths is an optional list of strings of preprocessing functions to apply to the images
  "preprocess": [
    # grayscale changes the image to grayscale before processing  
    "grayscale"
  ],
  # detect is an object of label->confidence matches that will be applied to the entire image
  # The "*" for the label name indicates it can match any label. If a specific label is listed
  # than it cannot be matched by the wildcard. This example matches any label at 50% confidence
  # and only car if it's confidence is over 60%.
  "detect": {
    "*": 50,
    "car": 60
  },
  # The regions array is a list of specific matches for areas within your image/video stream.
  # When processing rules, the first detection rule to match wins. 
  "regions": [
    # The top,left,bottom and right are float values from 0..1 that indicate a bounding box to look
    # for object detections. They are based on the image size. A 400x300 image with a bounding box
    # as shown in the example blow would look for objects inside the box of
    # {top: 300*0.1 = 30, left: 400*0.1 = 40, bottom: 300*0.9 = 270, right: 400*0.9 = 360}
    # The detect object is exactly how it's described above in the global detection option.
    # The covers boolean indicates if this region must completely cover the detected object or 
    # not. If covers = true, then the detcted object must be completely inside of this region to match.
    # If covers = false than if any part of this object is inside of this region, it will match.
    {"top": 0.1, "left": 0.1, "bottom": 0.9, "right": 0.9, "detect": {"*":50}, "covers": false}
    ...
  ]
}  
```

## DETECT RESPONSE
```json
{
  # This is the ID passed in the detect request.
  "id": "whatever",
  # If you specified a value for image in the detection request, this is the base64 encoded imge
  # returned from the detection. It has all of the detectons bounding boxes marked with label and 
  # confidence.
  "image": "b64 data...",
  # Detections is a list of all of the objects detected in the image after being passed through 
  # all of the filters. The top,left,bottom and right values are floats from 0..1 describing a 
  # bounding box of the object in the image. The label of the object and the confidence from 0..100
  # are also provided.
  "detections": [
    {"top": 0.1, "left": 0.1, "bottom": 0.9, "right": 0.9, "label": "dog", "confidence": 90.0 }
    ...
  ],
  # Any errors detected in the processing
  "error": "any errors"
}


```
## GET /
If you just browse to the DOODS2 endpoint you will be presented with a very simple UI for testing and
working with DOODS. It allows you to upload an image and test settings as well as kick off streaming
video processes to monitor results in realtime as you tune your settings.

## GET /detectors
This API call returns the configured detectors on DOODS and includes the list of labels that each detector supports.

## POST /detect
This API call takes a JSON [Detect Request](#detect-request) in the POST body and returns a JSON [Detect Response](#detect-response)
with the detections.

## POST /image
This API call takes a JSON [Detect Request](#detect-request) in the POST body and returns an image as specified in the 
image propert of the Detect Request with all of the bounding boxes drawn with labels and confidence. This is equivalent
of calling the POST /detect endpoint but only returning the image rather than all of the detection information as well.

## GET /stream?detection_request=<URL Encoded Detect Request JSON>
This endpoint takes a URL Encoded JSON [Detect Request](#detect-request) document as the `detect_request` query parameter. It expected the `data`
value of the Detect Request to be a streaming video URL (like `rtsp://...`) It will connect to the stream and continuously
process detections as fast as it can (or as dictated by the `throttle` parameter) and returns an MJPEG video stream
suitable for viewing in most browsers. It's useful for testing. 

## WS /stream
This is a websocket endpoint where once connected expects you to send a single JSON [Detect Request](#detect-request). 
In the request it's expected that the `data` parameter will be a streaming video URL (like `rtsp://...`) It will 
connect to the stream and continuously process detections as fast as it can (or as dictated by the `throttle` parameter).
It will return JSON [Detect Response](#detect-response) every time it processes a frame. Additionally, if you specified
a value for the `image` parameter, it will include the base64 encoded image in the `image` part of the response with
the bounding boxes, labels and confidence marked.

## Configuraton Format

TODO

## EdgeTPU
DOODS2 supports the EdgeTPU hardware accelerator. This requires Tensorflow lite `edgetpu.tflite` models.

## Supported Detectors
There are currently 3 supported dectector formats
- tflite - Tensorflow lite `.tflite` models
- tensorflow - Original tensoflow frozen models (Usually end with `.pb`)
- tensorflow2 - Tensorflow 2 object detection modes. (Points to a directory with information)

