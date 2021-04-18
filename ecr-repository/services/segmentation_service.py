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

    def run(self, body):
        # converting from string to map
        body = json.loads(body)
        wait_url = body['url_image']

        try:
            # download s3 image
            _file_path = download_image(wait_url)  
            body['local_image'] = _file_path

            # run the file with the segmentation script in parallel
            os.system('python %s -sm %s -f %s' % (os.path.join(os.getcwd(), os.environ.get('SEGMENTATION_ACTION')), self._segmentation_model_path, _file_path))

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
            delete_standby_image(wait_url)

        return body
