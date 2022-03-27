from tensorflow.lite.python.interpreter import Interpreter
import numpy as np
import cv2
import odrpc
import logging
import threading
from config import DoodsDetectorConfig
from detectors.labels import load_labels

input_mean = 127.5
input_std = 127.5

class TensorflowLite:
    def __init__(self, config: DoodsDetectorConfig):
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'tflite',
            'labels': [],
            'model': config.modelFile,
        })
        self.hwAccel = config.hwAccel
        self.logger = logging.getLogger("doods.tflite."+config.name)
        self.mutex = threading.Lock()
        self.interpreter_available = threading.Condition(self.mutex)
        self.interpreters = []
        self.numThreads = config.numThreads
        self.poolSize = 1

        if self.numThreads < 1:
            raise ValueError('numThreads must be greater than or equal to 1')

        # Build the first interpreter
        interpreter = self.buildInterpreter()

        self.interpreters.append(interpreter)

        # Get model details
        self.input_details = interpreter.get_input_details()
        self.output_details = interpreter.get_output_details()
        self.config.height = self.input_details[0]['shape'][1]
        self.config.width = self.input_details[0]['shape'][2]
        self.floating_model = (self.input_details[0]['dtype'] == np.float32)

        # Load labels
        self.labels = load_labels(config.labelFile)
        for i in self.labels:
            self.config.labels.append(self.labels[i])

    def buildInterpreter(self):
        # Load the Tensorflow Lite model.
        # If using Edge TPU, use special load_delegate argument
        if self.hwAccel:
            from tensorflow.lite.python.interpreter import load_delegate
            try:
                interpreter = Interpreter(model_path=self.config.model,
                    experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
            # This might fail the first time as this seems to load the drivers for the EdgeTPU the first time.
            # Doing it again will load the driver. 
            except ValueError:
                try:
                    interpreter = Interpreter(model_path=self.config.model,
                        experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
                except ValueError:
                    raise ValueError('Could not load EdgeTPU detector')
        else:
            interpreter = Interpreter(model_path=self.config.model)
        
        interpreter.allocate_tensors()
        return interpreter

    def detect(self, image):
       
        image_resized = cv2.resize(image, (self.config.width, self.config.height))
        input_data = np.expand_dims(image_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if self.floating_model:
            input_data = (np.float32(self.input_data) - input_mean) / input_std

        # Get an interpreter from the pool
        with self.mutex:
            if not self.interpreters:
                if self.poolSize < self.numThreads:
                    self.interpreters.append(self.buildInterpreter())
                    self.poolSize += 1
                else: 
                    self.interpreter_available.wait(None)
            interpreter = self.interpreters.pop()

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(self.input_details[0]['index'], input_data)
        interpreter.invoke()
        
        ret = odrpc.DetectResponse()

        # There is only one output in an image detector
        if len(self.output_details) == 1:
            scores = interpreter.get_tensor(self.output_details[0]['index'])[0] # Confidence of detected objects
            for i in range(len(scores)):
                detection = odrpc.Detection()
                (detection.top, detection.left, detection.bottom, detection.right) = [0,0,1,1]
                detection.confidence = scores[i] * 100.0
                if i in self.labels:
                    detection.label = self.labels[i]
                else:
                    detection.label = "unknown"
                ret.detections.append(detection)
        else:
            boxes = interpreter.get_tensor(self.output_details[0]['index'])[0] # Bounding box coordinates of detected objects
            classes = interpreter.get_tensor(self.output_details[1]['index'])[0] # Class index of detected objects
            scores = interpreter.get_tensor(self.output_details[2]['index'])[0] # Confidence of detected objects
            count = interpreter.get_tensor(self.output_details[3]['index'])[0] # Count of detections

            for i in range(int(count)):
                detection = odrpc.Detection()
                (detection.top, detection.left, detection.bottom, detection.right) = boxes[i].tolist()
                detection.confidence = scores[i] * 100.0
                if isinstance(classes[i], str):
                    detection.label = classes[i]
                elif int(classes[i]) in self.labels:
                    detection.label = self.labels[int(classes[i])]
                else:
                    detection.label = 'unknown:%s' % classes[i]
                ret.detections.append(detection)
        
        with self.mutex:
            self.interpreters.append(interpreter)
            self.interpreter_available.notify()

        return ret

