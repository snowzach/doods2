import numpy as np
import cv2
import odrpc
import logging
from config import DoodsDetectorConfig
from detectors.labels import load_labels
import torch
import sys
import torch.nn as nn
import time

# https://github.com/johnolafenwa/DeepStack/blob/dev/intelligencelayer/shared/process.py
class DeepStack:
    def __init__(self, config: DoodsDetectorConfig):
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'deepstack',
            'labels': [],
            'model': config.modelFile,
        })

        self.logger = logging.getLogger("doods.deepstack."+config.name)

        # Include the deepstack-trainer files
        sys.path.append('detectors/yolov5')

        self.device = torch.device("cuda:0" if config.hwAccel else "cpu")
        self.torch_model = torch.load(config.modelFile, map_location=self.device)["model"].float().fuse().eval()        
        self.labels = self.torch_model.names
        self.config.labels = self.torch_model.names

    def detect(self, image):
        (height, width) = image.shape[:2]
        (image, ratio, (dx, dy)) = letterbox(image)
        image = np.asarray(image) # Crop image
        image = image.transpose(2, 0, 1)
        image = np.ascontiguousarray(image)
        image = torch.from_numpy(image).to(self.device)
        image = image.float()
        image /= 255.0  # 0 - 255 to 0.0 - 1.0
        if image.ndimension() == 3:
            image = image.unsqueeze(0)

        # Run detection
        results = self.torch_model(image, augment=False)[0]
        results = non_max_suppression(results, 0.4, 0.45)[0]
        
        ret = odrpc.DetectResponse()
        if type(results) == type(None):
            return ret
        for *xyxy, conf, cls in results:
            detection = odrpc.Detection()
            (detection.top, detection.left, detection.bottom, detection.right) = ((xyxy[1]-dy)/(height*ratio[0]), (xyxy[0]-dx)/(width*ratio[0]), (xyxy[3]-dy)/(height*ratio[0]), (xyxy[2]-dx)/(width*ratio[0]))
            detection.confidence = conf.item() * 100.0
            detection.label = self.labels[int(cls.item())]
            ret.detections.append(detection)
        return ret

def letterbox(
    img,
    new_shape=(640, 640),
    color=(114, 114, 114),
    auto=True,
    scaleFill=False,
    scaleup=True,
):
    # Resize image to a 32-pixel-multiple rectangle https://github.com/ultralytics/yolov3/issues/232
    shape = img.shape[:2]  # current shape [height, width]

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better test mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios

    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, 32), np.mod(dh, 32)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border

    cv2.imwrite('test.jpg', img)

    return img, ratio, (dw, dh)

def non_max_suppression(
    prediction, conf_thres=0.1, iou_thres=0.6, agnostic=False
):
    """Performs Non-Maximum Suppression (NMS) on inference results
    Returns:
         detections with shape: nx6 (x1, y1, x2, y2, conf, cls)
    """

    nc = prediction[0].shape[1] - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    # Settings
    multi_label = nc > 1  # multiple labels per box (adds 0.5ms/img)

    output = [None] * prediction.shape[0]
    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        # x[((x[..., 2:4] < min_wh) | (x[..., 2:4] > max_wh)).any(1), 4] = 0  # width-height
        x = x[xc[xi]]  # confidence

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Compute conf
        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        # Box (center x, center y, width, height) to (x1, y1, x2, y2)
        box = xywh2xyxy(x[:, :4])

        # Detections matrix nx6 (xyxy, conf, cls)
        if multi_label:
            i, j = (x[:, 5:] > conf_thres).nonzero(as_tuple=False).T
            x = torch.cat((box[i], x[i, j + 5, None], j[:, None].float()), 1)
        else:  # best class only
            conf, j = x[:, 5:].max(1, keepdim=True)
            x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > conf_thres]

        # If none remain process next image
        n = x.shape[0]  # number of boxes
        if not n:
            continue

        # Batched NMS
        c = x[:, 5:6] * 4096 # max box height
        boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
        i = torch.ops.torchvision.nms(boxes, scores, iou_thres)
        
        output[xi] = x[i]

    return output

def xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = torch.zeros_like(x) if isinstance(x, torch.Tensor) else np.zeros_like(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y
