import os
import gc
import cv2
import json
import traceback
import skimage.io
import numpy as np
import tensorflow as tf
import keras.backend as K
K.set_image_data_format('channels_last')

from utils.sqs_utils import SQSProducer
from pixellib.instance import instance_segmentation
from utils.file_utils import download_image, add_collection_image, delete_standby_image, delete_local_tmp_imagem


class SegmentationService:
    
    def __init__(self):    
        self._service_name = 'SegmentationService'
        self._segmentation_model_path = os.environ.get('SEGMENTATION_MODEL')
        self._produce_prediction = SQSProducer(os.environ.get('PREDICT_QUEUE'), os.environ.get('AWS_REGION'))
        
    def get_name(self):
        return self._service_name

    def get_queue(self):
        return os.environ.get('SEQMENTATION_QUEUE')

    def _load_segmentation_model(self):
        _instance_segmentation = instance_segmentation()
        _instance_segmentation.load_model(self._segmentation_model_path)
        return _instance_segmentation

    def _get_silhouette(self, mask, file_path):
        image = skimage.io.imread(file_path)
        for i in range(mask.shape[2]):
            for j in range(image.shape[2]):
                image[:,:,j] = image[:,:,j] * mask[:,:,i]
        _, _segmented_img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)
        return _segmented_img

    def run(self, body):
        _instance_segmentation = None

        # converting from string to map
        body = json.loads(body)
        wait_url = body['url_image']

        try:
            # download s3 image
            _file_path = download_image(wait_url)  
            body['local_image'] = _file_path

            # load segmentation model
            _instance_segmentation = self._load_segmentation_model()

            # creates the segmentation target
            _target_classes = _instance_segmentation.select_target_classes(person=True)

            # target person in the image
            _mask, _ = _instance_segmentation.segmentImage(
                _file_path, 
                segment_target_classes=_target_classes, 
                extract_segmented_objects=True
            )

            # convert targeting values ​​to integer
            _mask = _mask['masks'].astype(int)

            # get silhouette of the person in the image and
            # save the new image in the local folder
            cv2.imwrite(_file_path, self._get_silhouette(_mask, _file_path))

            # saves the segmented image on s3
            body['url_image'] = add_collection_image(_file_path)

            # posts a message to the prediction queue with the 
            # local directory of the segmented image
            # Conditional: will not post the message when the flag isCollection is true
            if not body['isCollection']:
                self._produce_prediction.run(body)
                
        except Exception as e:
            if 'local_image' in body and os.path.exists(body['local_image']):
                delete_local_tmp_imagem(body['local_image'])
            print(traceback.format_exc())

        finally:
            if _instance_segmentation is not None:
                del _instance_segmentation
                tf.keras.backend.clear_session()
                gc.collect()
            delete_standby_image(wait_url)

        return body
