import odrpc
import logging
from ultralytics import YOLO as uYOLO
from config import DoodsDetectorConfig

class YOLO:
    def __init__(self, config: DoodsDetectorConfig):
        
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'yolo',
            'labels': [],
            'model': config.modelFile,
        })
        self.logger = logging.getLogger("doods.yolo."+config.name)
        self.model = uYOLO(config.modelFile.strip())
        if isinstance(self.model.names, dict):
            self.labels = list(self.model.names.values())
        else:
            self.labels = self.model.names
        self.config.labels = self.labels

    def detect(self, image):

        results = self.model.predict(source = image, verbose = True)
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
