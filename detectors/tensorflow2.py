import os
import logging
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import config_util
from object_detection.builders import model_builder
import numpy as np
import odrpc

class Tensorflow2:
    def __init__(self, config):
        self.config = odrpc.Detector(**{
            'name': config.name,
            'type': 'tensorflow2',
            'labels': [],
            'model': config.modelFile
        })
        self.logger = logging.getLogger("doods.tf2."+config.name)

        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # Suppress TensorFlow logging (1)
        tf.get_logger().setLevel('ERROR')           # Suppress TensorFlow logging (2)

        # Enable GPU dynamic memory allocation
        gpus = tf.config.experimental.list_physical_devices('GPU')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)

        # Load pipeline config and build a detection model
        PATH_TO_CKPT = os.path.join(config.modelFile, 'checkpoint/')
        PATH_TO_CFG = os.path.join(config.modelFile, 'pipeline.config')
        if not os.path.exists(PATH_TO_CKPT):
            raise Exception("Missing checkpoint file")

        configs = config_util.get_configs_from_pipeline_file(PATH_TO_CFG)
        model_config = configs['model']
        self.detection_model = model_builder.build(model_config=model_config, is_training=False)

        # Restore checkpoint - Do we need this
        ckpt = tf.compat.v2.train.Checkpoint(model=self.detection_model)
        ckpt.restore(os.path.join(PATH_TO_CKPT, 'ckpt-0')).expect_partial()

        if not os.path.exists(config.labelFile):
            raise Exception("Missing labels file")

        # Load the labels and put into the config
        self.category_index = label_map_util.create_category_index_from_labelmap(config.labelFile, use_display_name=True)
        for i in self.category_index:
            self.config.labels.append(self.category_index[i]['name'])

    # Tensorflow detection function
    @tf.function
    def detect_fn(self, image):
        """Detect objects in image."""
        image, shapes = self.detection_model.preprocess(image)
        prediction_dict = self.detection_model.predict(image, shapes)
        detections = self.detection_model.postprocess(prediction_dict, shapes)
        return detections, prediction_dict, tf.reshape(shapes, [-1])

    def detect(self, image):

        # (im_width, im_height) = image.size
        # image_np = np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)
        input_tensor = tf.convert_to_tensor(np.expand_dims(image, 0), dtype=tf.float32)

        detections, prediction_dict, shapes = self.detect_fn(input_tensor)

        boxes = detections['detection_boxes'].numpy()[0]
        scores = detections['detection_scores'].numpy()[0]
        classes = detections['detection_classes'].numpy()[0]

        ret = odrpc.DetectResponse()
        for i in range(len(boxes)):
            detection = odrpc.Detection()
            (detection.top, detection.left, detection.bottom, detection.right) = boxes[i].tolist()
            detection.confidence = scores[i] * 100.0
            if int(classes[i])+1 in self.category_index:
                detection.label = self.category_index[int(classes[i])+1]
            else:
                detection.label = 'unknown:%s' % classes[i]
            ret.detections.append(detection)

        return ret
