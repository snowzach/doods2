import odrpc
import logging
from ultralytics import YOLO as uYOLO
from config import DoodsDetectorConfig
from detectors.tflite import buildInterpreter

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
            interpreter = buildInterpreter(self.config.model, self.hwAccel)
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
