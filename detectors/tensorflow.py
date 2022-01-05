import tensorflow.compat.v1 as tf
import numpy as np
import cv2
import odrpc
from detectors.labels import load_labels

class Tensorflow:
    def __init__(self, config):
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'tensorflow2',
            'labels': [],
            'model': config.modelFile
        })

        self.detection_graph = Tensorflow.load_pb(config.modelFile)

        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        self.d_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        self.d_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        self.d_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_d = self.detection_graph.get_tensor_by_name('num_detections:0')
        self.sess = tf.Session(graph=self.detection_graph)

        self.labels = load_labels(config.labelFile)
        for i in self.labels:
            self.config.labels.append(self.labels[i])

        print(self.image_tensor.get_shape())

    def detect_fn(self, image):
        # Bounding Box Detection.
        with self.detection_graph.as_default():
            # Expand dimension since the model expects image to have shape [1, None, None, 3].
            img_expanded = np.expand_dims(image, axis=0)  
            (boxes, scores, classes, num) = self.sess.run(
                [self.d_boxes, self.d_scores, self.d_classes, self.num_d],
                feed_dict={self.image_tensor: img_expanded})
        return boxes[0], scores[0], classes[0], num[0]

    def detect(self, image):

        boxes, scores, classes, num = self.detect_fn(image)

        ret = odrpc.DetectResponse()
        for i in range(int(num)):
            detection = odrpc.Detection()
            (detection.top, detection.left, detection.bottom, detection.right) = boxes[i].tolist()
            detection.confidence = scores[i] * 100.0
            if int(classes[i]) in self.labels:                
                detection.label = self.labels[int(classes[i])]
            else:
                detection.label = "unknown"
            ret.detections.append(detection)
        return ret

    @staticmethod
    def load_pb(path_to_pb):
        with tf.gfile.GFile(path_to_pb, "rb") as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
        with tf.Graph().as_default() as graph:
            tf.import_graph_def(graph_def, name='')
            return graph


