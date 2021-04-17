import os
import skimage.io
import cv2
import math
import json
import traceback

from dotenv import load_dotenv
load_dotenv()

from utils.file_utils import download_image, add_collection_image, delete_standby_image, delete_local_tmp_imagem
from pixellib.instance import instance_segmentation

from keras.models import load_model
import keras.backend as K
K.set_image_data_format('channels_last')

from utils.sqs_utils import SQSConsumer, SQSProducer
from PIL import Image

from utils.db_utils import add_to_table

INSTANCE_SEGMENTATION = instance_segmentation()
INSTANCE_SEGMENTATION.load_model(os.environ.get('SEGMENTATION_MODEL'))
TARGET_CLASSES = INSTANCE_SEGMENTATION.select_target_classes(person=True)
MODEL = load_model(os.environ.get('POCKET_PARKINSON_MODEL'))
SEQMENTATION_QUEUE = os.environ.get('SEQMENTATION_QUEUE')
PREDICT_QUEUE = os.environ.get('PREDICT_QUEUE')
PREDICT_TABLE = os.environ.get('PREDICT_TABLE')

class SegmentationService:
    name = 'SegmentationService'

    def _get_silhouette(self, mask, file_path):
        image = skimage.io.imread(file_path)
        
        for i in range(mask.shape[2]):
            for j in range(image.shape[2]):
                image[:,:,j] = image[:,:,j] * mask[:,:,i]
        _, _segmented_img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)
        return _segmented_img

    @SQSConsumer(SEQMENTATION_QUEUE)
    def handle_message(self, body):
        try:
            body = json.loads(body)
            print('Segmentation Queue Consume - ID:', body['predictid'], '- index:', body['index'])
            
            # download s3 image
            # _file_path = download_image(body['url_image'])  
            _file_path = '/home/ubuntu/pocket-parkinson-serverless/ecr-repository/tmp/teste.png'

            # target person in the image
            _mask, _ = INSTANCE_SEGMENTATION.segmentImage(
                _file_path, 
                segment_target_classes=TARGET_CLASSES, 
                extract_segmented_objects=True
            )

            # convert targeting values ​​to integer
            _mask = _mask['masks'].astype(int)

            # get silhouette of the person in the image and
            # save the new image in the local folder
            cv2.imwrite(_file_path, self._get_silhouette(_mask, _file_path))

            # remove s3 standby
            # delete_standby_image(body['url_image'])

            # saves the segmented image on s3
            # body['url_image'] = add_collection_image(_file_path)

            # posts a message to the prediction queue with the 
            # local directory of the segmented image
            # Conditional: will not post the message when the flag isCollection is true
            # if not body['isCollection']:
            #     body['local_image'] = _file_path
            #     SQSProducer(PREDICT_QUEUE, body)
        except Exception as e:
            print('Segmentation Queue Consume - Error:', str(e))
            print(traceback.format_exc())

class PredictionService:
    name = 'PredictionService'

    def _inv_softmax(self, x):
        return (K.log(x) + K.log(math.log(10.))).numpy()[0]

    def _convert_output(self, predict_value):
        _converted_values = self._inv_softmax(predict_value)
        _prediction_category = np.argmax(predict_value, axis=1)[0]
        return str(_converted_values[_prediction_category] * 100), int(_prediction_category == 1)

    def _convert_image(self, file_path):
        _image = Image.open(_file_path)
        _image = _image.convert('RGB')
        _image = _image.resize((150,150))
        return np.array([np.asarray(_image)]) / 255.0

    @SQSConsumer(PREDICT_QUEUE)
    def handle_message(self, body):
        try:
            body = json.loads(body)
            print('Predict Queue Consume - ID:', body['predictid'], '- index:', body['index'])

            # get the path of the local file
            _file_path = body['local_image']

            # predict the local image
            # 0 - others
            # 1 - parkinson 
            _predict = MODEL.predict(self._convert_image(_file_path))

            # remove local temporary image
            delete_local_tmp_imagem(_file_path)

            # convert results
            _porcentage, _isParkinson = _convert_output(_predict)

            # save data to the database
            add_to_table(PREDICT_TABLE, {
                'predictid': body['predictid'],
                'patientid': body['patientid'],
                'index': body['index'],
                'image': body['url_image'],
                'isParkinson': _isParkinson,
                'percentage': _porcentage
            })
        except Exception as e:
            print('Predict Queue Consume - Error:', str(e))
            print(traceback.format_exc())