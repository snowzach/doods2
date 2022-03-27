# DOODS2 - Return of DOODS
Dedicated Open Object Detection Service - Yes, it's a backronym...

DOODS is a REST service that detects objects in images or video streams. It's designed to be very easy to use, run as a container and available remotely.
It also supports GPUs and EdgeTPU hardware acceleration.

DOODS2 is a rewrite of [DOODS](https://github.com/snowzach/doods) in Python. It supports the exact same
REST api endpoints as the original DOODS but it also includes endpoints for handling streaming feeds with realtime
feedback as annotated video and websocket JSON detection data.

Why Python you may ask... Well, lots of machine learning stuff is in Python and there is pretty good support for
Object Detection and helpers in Python. Maintaining the code in Go was a huge pain. 
DOODS2 is designed to have a compatible API specification with DOODS as well as adding some additional features. 
It's my hope that in Python I might get a little more interest from the community in maintaining it and adding features.

DOODS2 drops support for gRPC as I doubt very much anyone used it anyways.

# Quickstart in Docker
On your local machine run: `docker run -it -p 8080:8080 snowzach/doods2:latest` and open a browser to http://localhost:8080 
Try uploading an image file or passing it an RTSP video stream. You can make changes to the specification by referencing the [Detect Request](#detect-request) payload.

Three detectors are included with the base image that you can try.
- default - coco_ssd_mobilenet_v1_1.0_quant.tflite - A decent and fast Tensorflow light object detector.
- tensorflow - faster_rcnn_inception_v2_coco_2018_01_28.pb - A much slower but more accurate Tensorflow object detector.
- yolov5s - https://github.com/ultralytics/yolov5 yolo V5 model - A fast and accurate detector

## Docker Images
DOODS2 is distributed in a docker image. There are several tags you can reference to pick the image you like.
- armv7l - 32 bit ARM devices with a v7 CPU like the Raspberry Pi
  - Does not include PyTorch or Tensorflow Object Detection
- aarch64 - 64 bit ARM devices with a v8 CPU (Raspberry Pi 64 bit, ODroid, etc)
  - Does not include PyTorch or Tensorflow Object Detection
- noavx - 64 bit x86_64 architecture WITHOUT avx support. This should run on just about everything.
- latest - The `latest` tag references the above 3 tags so if you pick latest it should work on just about everything.

Additional more optimized tags are available:
- amd64 - 64 bit x86_64 architecture WITH avx support. This should be faster than the noavx image on newer processors.
- amd64-gpu - 64 bit x86_64 architecture with NVidia GPU support. See the section below on how to run this.

# REST API
The REST API has several endpoints for detecting objects in images as well as streams. Details of the payloads and endpoints are below.

## DETECT REQUEST
Every request to DOODS involves the Detect Request JSON object that looks like this.
```jsonc
{
  // This ID field is user definable and will return the same ID that was passed in.
  "id": "whatever",
  // This is the name of the detector to be used for this detection. If not specified, 'default' will be used if it exists.
  "detector_name": "default",
  // Data is either base64 encoded image data for a single image, it may also be a URL to an image
  // For a stream it's expected to be a URL that can be read by ffmpeg. `rtsp://..` or `http://..` is typical.
  // You can also provide a video URL to detect a single image. It will grab a single frame from the source to 
  // run detection on. (It may be kinda slow though)
  "data": "b64 or url",
  // The image option determines, for API calls that return an image, what format the image should be.
  // Supported options currently are "jpeg" and "png"
  "image": "jpeg",
  // The throtle option determines, for streaming API calls only, how often it should return results
  // in seconds. For example, 5 means return 1 result about every 5 seconds. A value of 0 indicates
  // it should return results as fast as it can. 
  "throttle": 5,
  // Ths is an optional list of strings of preprocessing functions to apply to the images. Each supported
  // option is listed below.
  "preprocess": [
    // grayscale = changes the image to grayscale before processing  
    "grayscale"
  ],
  // detect is an object of label->confidence matches that will be applied to the entire image
  // The "*" for the label name indicates it can match any label. If a specific label is listed
  // then it cannot be matched by the wildcard. This example matches any label at 50% confidence
  // and only car if it's confidence is over 60%.
  "detect": {
    "*": 50,
    "car": 60
  },
  // The regions array is a list of specific matches for areas within your image/video stream.
  // When processing rules, the first detection rule to match wins. 
  "regions": [
    // The top,left,bottom and right are float values from 0..1 that indicate a bounding box to look
    // for object detections. They are based on the image size. A 400x300 image with a bounding box
    // as shown in the example blow would look for objects inside the box of
    // {top: 300*0.1 = 30, left: 400*0.1 = 40, bottom: 300*0.9 = 270, right: 400*0.9 = 360}
    // The detect field is exactly how it's described above in the global detection option for you
    // to specify the labels that you wish to match. 
    // The covers boolean indicates if this region must completely cover the detected object or 
    // not. If covers = true, then the detcted object must be completely inside of this region to match.
    // If covers = false than if any part of this object is inside of this region, it will match.
    // If defined, the optional id field will be included in detections that this region matched.  NOTE: 
    // only the first region (including the global detection) to match an object will be used.
    {"id": "someregion", "top": 0.1, "left": 0.1, "bottom": 0.9, "right": 0.9, "detect": {"*":50}, "covers": false}
    ...
  ],

  // NOTE: Below fields are only available in requests configured as part of the MQTT configuration

  // If separate_detections is true each detected object will be published separately into 
  // a sub-topic based on its type (e.g doods/detect/requestid/regionid/person).  When False, the default,
  // the whole DetectResponse object will be published to the request topic (e.g. doods/detect/requestid).
  "separate_detections" : false,
  // If crop is true and separate_detections is true requested images will be cropped to 
  // the decection box.  Has no effect if separate_detections is false.
  "crop": false,
  // If binary_images is true requested images will be pubished as binary data 
  // to a separate topic (e.g. doods/image/requestid) instead of base64 encoded into the response.
  "binary_images" : false,
}  
```

## DETECT RESPONSE
```jsonc
{
  // This is the ID passed in the detect request.
  "id": "whatever",
  // If you specified a value for image in the detection request, this is the base64 encoded imge
  // returned from the detection. It has all of the detectons bounding boxes marked with label and 
  // confidence.
  "image": "b64 data...",
  // Detections is a list of all of the objects detected in the image after being passed through 
  // all of the filters. The top,left,bottom and right values are floats from 0..1 describing a 
  // bounding box of the object in the image. The label of the object and the confidence from 0..100
  // are also provided.
  "detections": [
    {"top": 0.1, "left": 0.1, "bottom": 0.9, "right": 0.9, "label": "dog", "confidence": 90.0 }
    ...
  ],
  // Any errors detected in the processing
  "error": "any errors"
}
```

## API Endpoints

### GET - /
If you just browse to the DOODS2 endpoint you will be presented with a very simple UI for testing and
working with DOODS. It allows you to upload an image and test settings as well as kick off streaming
video processes to monitor results in realtime as you tune your settings.

### GET - /detectors
This API call returns the configured detectors on DOODS and includes the list of labels that each detector supports.

### POST - /detect
This API call takes a JSON [Detect Request](#detect-request) in the POST body and returns a JSON [Detect Response](#detect-response)
with the detections.

### WS - /detect
This is a websocket endpoint that works exactly how the `/detect` API works except that you may
send in many JSON [Detect Request](#detect-request) messages and it will process them asynchronously
and return the responses. You should use unique `id` field values in the request to tell the responses 
apart.

### POST /image
This API call takes a JSON [Detect Request](#detect-request) in the POST body and returns an image as specified in the 
image propert of the Detect Request with all of the bounding boxes drawn with labels and confidence. This is equivalent
of calling the POST /detect endpoint but only returning the image rather than all of the detection information as well.

### GET /stream?detection_request=<URL Encoded Detect Request JSON>
This endpoint takes a URL Encoded JSON [Detect Request](#detect-request) document as the `detect_request` query parameter. It expected the `data`
value of the Detect Request to be a streaming video URL (like `rtsp://...`) It will connect to the stream and continuously
process detections as fast as it can (or as dictated by the `throttle` parameter) and returns an MJPEG video stream
suitable for viewing in most browsers. It's useful for testing. 

### WS /stream
This is a websocket endpoint where once connected expects you to send a single JSON [Detect Request](#detect-request). 
In the request it's expected that the `data` parameter will be a streaming video URL (like `rtsp://...`) It will 
connect to the stream and continuously process detections as fast as it can (or as dictated by the `throttle` parameter).
It will return JSON [Detect Response](#detect-response) every time it processes a frame. Additionally, if you specified
a value for the `image` parameter, it will include the base64 encoded image in the `image` part of the response with
the bounding boxes, labels and confidence marked.

# Configuraton Format
DOODS requires a YAML configuration file to operate. There is a built in default configuration in the docker image
that references built in default models. The configuration file looks like this by default.

```yaml
server:
  host: 0.0.0.0
  port: 8080
  metrics: true
logging:
  level: info
doods:
  log: detections
  boxes:
    enabled: True
    boxColor: [0, 255, 0]
    boxThickness: 1
    fontScale: 1.2
    fontColor: [0, 255, 0]
    fontThickness: 1
  regions:
    enabled: True
    boxColor: [255, 0, 255]
    boxThickness: 1
    fontScale: 1.2
    fontColor: [255, 0, 255]
    fontThickness: 1
  globals:
    enabled: True
    fontScale: 1.2
    fontColor: [255, 255, 0]
    fontThickness: 1
  detectors:
    - name: default
      type: tflite
      modelFile: models/coco_ssd_mobilenet_v1_1.0_quant.tflite
      labelFile: models/coco_labels0.txt
      hwAccel: false
      numThreads: 4
    - name: tensorflow
      type: tensorflow
      modelFile: models/faster_rcnn_inception_v2_coco_2018_01_28.pb
      labelFile: models/coco_labels1.txt
      hwAccel: false
```

You can pass a new configuration file using an environment variable `CONFIG_FILE`. There is also a `--config` and `-c` command line option.
for passing a configuration file. The environment variable takes precedences if set. Otherwise it defaults to looking for a `config.yaml` in the
current directory.

Configuration options can also be set with environment variables using the value in all caps separated by underscore. For example
you can set `SERVER_HOST=127.0.0.1` to only listen on localhost. Setting the doods detectors must be done with a config file.

## Server
This allows you to set the host and port the DOODS2 server listens on.

## Logging
This lets you set the logging level of the server.

## DOODS - log
This lets you set the logging of detections. 
`detections` - Log detections (default)
`all` - Log ALL detections (before apply the filters for regions, labels, etc)

## DOODS - boxes
The boxes allows you to set if, when requesting an image be returned, will the detections be drawn with bounding boxes. 
The defaults are shown above. You can disable the boxes as well as set the box color and line thickness. The color is specified
as a 3 value list of RGB values. The font scale, thickness and color can be set seprately.

## DOODS - regions, globals
This allows you to annotate returned images with the requested regions and global detection regions that you are scanning for in images.
You could use this to debug and then disable them when you are done if you don't want to see them in your images.

# EdgeTPU
DOODS2 supports the EdgeTPU hardware accelerator. This requires Tensorflow lite `edgetpu.tflite` models.
In the config you need to set the `hwAccel` boolean to true for the model and it will load the edgeTPU driver and model.
As well, you will need to pass the edgeTPU device to DOODS. This is typically done with the docker flag `--device=/dev/bus/usb`
or in a docker-compose file with:
```yaml
version: '3.2'
services:
  doods:
    image: snowzach/doods2:amd64-gpu
    ports:
      - "8080:8080"
    devices:
      - /dev/bus/usb
```

You can download models for the edgeTPU here: https://coral.ai/models/object-detection

# GPU Support
NVidia GPU support is available in the `:amd64-gpu` tagged image. This requires the host machine have NVidia CUDA installed as well as
Docker 19.03 and above with the `nvidia-container-toolkit`. 

See this page on how to install the CUDA drives and the container toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

You need to tell docker to pass the GPU through for DOODS to use. You can do this with the docker run command by adding `--gpus all` to the command.
You can also do this with docker-compose by adding this to the DOODS container specification:
```yaml
version: '3.2'
services:
  doods:
    image: snowzach/doods2:amd64-gpu
    ports:
      - "8080:8080"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

# Supported Detectors / Models
There are currently 3 supported dectector formats
- tflite - Tensorflow lite `.tflite` models
- tensorflow - Original tensoflow frozen models (Usually end with `.pb`)
- pytorch - PyTorch based models like yolo
- deepstack - Deepstack models suppor
- tensorflow2 - DISABLED - The libraries required were huge (2.2GB) and it was too slow to be ussful for the time being.
  
## Tensorflow Lite - .tflite 
Just download the file, make it available to dudes and put the path to the tflite model file
in for the `modelFile` config option and the path to the text `labelsFile` in the config option. You can also set 
`hwAccel` if it's an `edgetpu.tflite` and of course you actually have a EdgeTPU connected.

Tensorflow Lite is the one type you can use the `numThreads` argument with and it will create a pool of tflite models for
which to run detections. You can create as many as you want.

## Tensorflow 1 - .pb
These are protobuf files that end in .pb. You just need to download them and usually un-tgz the archive and get the `.pb` file
and provide it to DOODS along with the labels file. 

There's a good list of these here: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf1_detection_zoo.md

## PyTorch - Automatically load from Torch Hub
This allows you to pull models directly from github using the torch.hub system. https://pytorch.org/docs/stable/hub.html

To configure these, for the model file specify the hub name and then the model separated by a comma. It will download and 
load the model. 

Example:
`modelFile: ultralytics/yolov5,yolov5s`

This is the PyTorch Hub https://pytorch.org/hub/ DOODS really only supports model detection models. All models may
not work yet as I work out the shape of the detections.

If you want to cache the models that are downloaded, you can set the environment variable `TORCH_HOME` and the models
will be stored at `$TORCH_HOME/hub`. (The default is /root/.cache/torch). 

## Deepstack - PyTorch .pt files
Deepstack is a pretty slick system that works pretty similar to the way that DOODS operates. There are quite a few models that
have been custom trained. There are some samples here: https://docs.deepstack.cc/custom-models-samples/
All you need to do is download the .pt files and list them as the model file in the config. The labels seems to be embedded.

If you receive a message that says `No module named 'models.yolo'` you are using a model that expects a very specific directory
layout. You can fix the issue by downloading this file into your models directory adjacent to your model:
`https://raw.githubusercontent.com/johnolafenwa/deepstack-trainer/main/models/yolo.py` This should resolve your issue.

## Tensorflow 2 - Model Directory
REMOVED: The dependencies for Tensorflow 2 Object detection were massive and it was really slow so I removed it for the time being.

Tensorflow 2 models are a little more complex and have a directory of files that you must pass into DOODS. You can download the file
and extract it to it's directory. For the `modelFile` option pass the path to the directory. You will need to download the labels file
as well and provide it's path in the `labelsFile` option.

This is a model zoo for Tensorflow 2 models: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md

I think they are better but they generally are much slower and probably require a GPU to work in a reasonable amount of time.