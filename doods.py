import base64
import logging
import numpy as np
import cv2
import odrpc

from detectors.tensorflow import Tensorflow
from detectors.tflite import TensorflowLite

logger = logging.getLogger('doods.doods')

# dict from detector type to class
detectors = {
    "tflite": TensorflowLite,
    "tensorflow": Tensorflow,
}

try:
    from detectors.pytorch import PyTorch
    detectors['pytorch'] = PyTorch
except ModuleNotFoundError:
    logger.info('PyTorch not installed...')

try:
    from detectors.deepstack import DeepStack
    detectors['deepstack'] = DeepStack
except ModuleNotFoundError:
    logger.info('DeepStack not installed...')

try:
    from detectors.tensorflow2 import Tensorflow2
    detectors['tensorflow2'] = Tensorflow2
except ModuleNotFoundError:
    logger.info("Tensorflow2 Object Detection API not installed...")

font                   = cv2.FONT_HERSHEY_PLAIN
fontScale              = 1.2
thickness              = 1
lineType               = 4

# These are the valid types and the conversion to what cv2 needs.
detect_request_image_conversion = {
    'true'      : '.jpg',
    '.jpg'      : '.jpg',
    'jpg'       : '.jpg',
    'jpeg'      : '.jpg',
    'image/jpeg': '.jpg',
    '.png'      : '.png',
    'png'       : '.png',
    'image/png' : '.png',
}

detectors_load_precedence = [
    "tflite",
    "tensorflow",
    "tensorflow2",
    "deepstack",
    "pytorch",
]

class MissingDetector:
    def __init__(self, dconfig):
        raise Exception('Unknown detector type %s.' % dconfig.type)

class Doods:
    def __init__(self, config):
        self.config = config

        self.config.detectors = sorted(self.config.detectors, key=lambda d: detectors_load_precedence.index(d.type) if d.type in detectors_load_precedence else 99)

        # Initialize the detectors
        self._detectors = {}
        for detector_config in self.config.detectors:
            detector_class = detectors.get(detector_config.type, MissingDetector)
            try:
                detector = detector_class(detector_config)
            except Exception as e:
                logger.error('Could not create detector %s/%s: %s' % (detector_config.type, detector_config.name, e))
                continue
            logger.info('Registered detector type:%s name:%s', detector.config.type, detector.config.name)
            self._detectors[detector_config.name] = detector

    # Get the detectors configs
    def detectors(self):
        detectors = []
        for name in self._detectors:
            detectors.append(self._detectors[name].config)
        return detectors

    # Detect image
    def detect(self, detect):
        # Coerce the image output type into something we like
        if detect.image:
            detect.image = detect_request_image_conversion.get(detect.image, '')

        # Get the detector
        if not detect.detector_name:
            detect.detector_name = 'default'
        if not detect.detector_name in self._detectors:
            return odrpc.DetectResponse(error="unknown detector name: %s" % detect.detector_name)
        detector = self._detectors[detect.detector_name]
        if not detector:
            ret = odrpc.DetectResponse
            ret.error = "could not determine detector"
            return ret

        # Already an image
        if type(detect.data) is np.ndarray:
            image = detect.data

        # If it's a url, use cv2 to read an image or frame.
        elif detect.data.startswith("http") or detect.data.startswith("rtsp") or detect.data.startswith("ftp"):
            cap = cv2.VideoCapture(detect.data)
            if cap.isOpened():
                _, image = cap.read()
                cap.release()
            else:
                raise 'No Image'
        
        # Should be base64 encoded image
        else:
            # Decode the image
            image_data = base64.b64decode(detect.data)
            image_bytes = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        
        # Handle preprocessing
        for process in detect.preprocess:
            if process == 'grayscale':
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                raise ValueError('unknown preprocessing request: %s' % process)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Run detection
        ret = detector.detect(image)
        if ret.error:
            return ret

        # Set the id        
        ret.id = detect.id
        # Sort the detections by confidence
        ret.detections = sorted(ret.detections, key=lambda d: d.confidence, reverse=True)

        if self.config.log == 'all':
            logger.info(ret)

        ret.detections = Doods.filter_detections(ret.detections, detect.detect, detect.regions)

        if self.config.log == 'detections':
            logger.info(ret)

        # If no image was requested, return the detection object
        if not detect.image:
            return ret

        # Convert the image back to BGR for saving
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        height, width, channels = image.shape

        # Draw the global detection labels
        if self.config.globals.enabled:
            global_labels = []
            for label in detect.detect:
                global_labels.append("%s:%d" % (label, detect.detect[label]))
            if len(global_labels) > 0:
                cv2.putText(image, ','.join(global_labels), (5, 15), font, 
                    self.config.globals.fontScale, tuple(self.config.globals.fontColor), self.config.globals.fontThickness, lineType)

        # Draw the region detection labels
        if self.config.regions.enabled:
            for region in detect.regions:
                region_labels = []
                for label in region.detect:
                    region_labels.append("%s:%d" % (label, region.detect[label]))
                cv2.putText(image, ','.join(region_labels), (int(region.left*width), int(region.top*height)-2), 
                    font, self.config.regions.fontScale, tuple(self.config.regions.fontColor), self.config.regions.fontThickness, lineType)
                cv2.rectangle(image, (int(region.left*width), int(region.top*height)), (int(region.right*width), int(region.bottom*height)), 
                    color=tuple(self.config.regions.boxColor), thickness=self.config.regions.boxThickness)

        # Draw the detections
        if self.config.boxes.enabled:
            for detection in ret.detections:
                cv2.putText(image, "%s:%d" % (detection.label, detection.confidence), (int(detection.left*width), int(detection.bottom*height)-2), 
                    font, self.config.boxes.fontScale, tuple(self.config.boxes.fontColor), self.config.boxes.fontThickness, lineType)
                cv2.rectangle(image, (int(detection.left*width), int(detection.top*height)), (int(detection.right*width), int(detection.bottom*height)), 
                    color=tuple(self.config.boxes.boxColor), thickness=self.config.boxes.boxThickness)

        ret.image = cv2.imencode(detect.image, image)[1].tostring()
        return ret

    # Filter the detections to the matches
    @staticmethod
    def filter_detections(detections, detect, regions):
        ret = {}
        for i, d in enumerate(detections):
            if d.label in detect:
                if d.confidence >= detect[d.label]:
                    ret[i] = d
                    continue
            elif '*' in detect and d.confidence >= detect['*']:
                ret[i] = d
                continue
            for r in regions:
                if (
                    ( r.covers and r.top <= d.top and r.left <= d.left and r.bottom >= d.bottom and r.right >= d.right ) or
                    ( not r.covers and d.top <= r.bottom and d.left <= r.right and d.bottom >= r.top and d.right >= r.left )
                ):
                    if d.label in r.detect:
                        if d.confidence >= r.detect[d.label]:
                            ret[i] = d
                            ret[i].region_id = r.id # Add ID of region for which this passed filters.
                            break
                    elif '*' in r.detect and d.confidence >= r.detect['*']:
                        ret[i] = d
                        ret[i].region_id = r.id # Add ID of region for which this passed filters.
                        break
        return list(ret.values())
