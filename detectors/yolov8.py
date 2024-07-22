from ultralytics import YOLO
from config import DoodsDetectorConfig

class YOLOv8:
    def __init__(self, config: DoodsDetectorConfig):
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'yolov8',
            'labels': [],
            'model': config.modelFile,
        })
        self.logger = logging.getLogger("doods.yolov8."+config.name)
        self.device = torch.device("cuda:0" if config.hwAccel else "cpu")
        repo, modelName = config.modelFile.split(',',1)
        self.torch_model = torch.hub.load(repo.strip(), modelName.strip())
        self.model = YOLO(config.modelFile.strip())
        self.labels = self.model.names
        self.config.labels = self.labels

    def detect(self, image):

        results = model.predict(source = image, verbose = True)
        (height, width, colors) = image.shape

        ret = odrpc.DetectResponse()

        for box in results[0].boxes:
            (detection.top, detection.left, detection.bottom, detection.right) = box.xyxy.numpy()
            detection.confidence = box.conf.numpy()
            detection.label = self.labels[result['cls'].numpy()]
            ret.detections.append(detection)
    
        return ret
