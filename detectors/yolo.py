import odrpc
import logging
from ultralytics import YOLO as uYOLO
from config import DoodsDetectorConfig
from tensorflow.lite.python.interpreter import Interpreter

class YOLO:
    def __init__(self, config: DoodsDetectorConfig):
        
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'yolo',
            'labels': [],
            'model': config.modelFile,
        })
        self.hwAccel = config.hwAccel
        self.predict_args = {}

        self.logger = logging.getLogger("doods.yolo."+config.name)
        self.model = uYOLO(config.modelFile.strip(),task='detect')
        if isinstance(self.model.names, dict):
            self.labels = list(self.model.names.values())
        else:
            self.labels = self.model.names
        self.config.labels = self.labels

        # If using a tflite model, retrieve the imgsz from an interpreter
        if self.config.model.endswith('.tflite'):
            interpreter = self.buildTfliteInterpreter()
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()
            img_height, img_width = input_details[0]['shape'][1:3]
            self.predict_args['imgsz'] = [img_height, img_width]

    def detect(self, image):
        results = self.model.predict(source = image, verbose = True, **self.predict_args)
        (height, width, colors) = image.shape

        ret = odrpc.DetectResponse()

        for box in results[0].boxes:
            detection = odrpc.Detection()
            (detection.left, detection.top, detection.right, detection.bottom) = box.xyxy.numpy().tolist()[0]
            detection.top = detection.top / height
            detection.bottom = detection.bottom / height
            detection.left = detection.left / width
            detection.right = detection.right / width
            detection.confidence = box.conf.item() * 100.0
            detection.label = self.labels[int(box.cls.item())]
            ret.detections.append(detection)
    
        return ret
    
    # Builds a tflite interpreter (a duplicate of the function in tflite.py)
    def buildTfliteInterpreter(self):
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
