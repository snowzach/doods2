import numpy as np
import cv2
import odrpc
import logging
from config import DoodsDetectorConfig
from detectors.labels import load_labels
import torch

class PyTorch:
    def __init__(self, config: DoodsDetectorConfig):
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'pytorch',
            'labels': [],
            'model': config.modelFile,
        })
        self.logger = logging.getLogger("doods.pytorch."+config.name)
        self.device = torch.device("cuda:0" if config.hwAccel else "cpu")
        repo, modelName = config.modelFile.split(',',1)
        self.torch_model = torch.hub.load(repo.strip(), modelName.strip())
        self.labels = self.torch_model.names
        self.config.labels = self.torch_model.names

    def detect(self, image):

        results = self.torch_model(image).pandas().xyxy[0]
        (height, width, colors) = image.shape

        ret = odrpc.DetectResponse()

        for result in results.to_dict(orient="records"):
            detection = odrpc.Detection()
            (detection.top, detection.left, detection.bottom, detection.right) = (result['ymin']/height, result['xmin']/width, result['ymax']/height, result['xmax']/width)
            detection.confidence = result['confidence'] * 100.0
            detection.label = result['name']
            ret.detections.append(detection)
    
        return ret
