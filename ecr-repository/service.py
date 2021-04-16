import os
import skimage.io
import cv2
import json

from dotenv import load_dotenv
load_dotenv()

from file_utils import clear_tmp, create_tmp_image, to_byte_str
from pixellib.instance import instance_segmentation
from keras.models import load_model
from keras import backend
backend.set_image_data_format("channels_last")
from sqs_utils import SQSConsumer
from PIL import Image

INSTANCE_SEGMENTATION = instance_segmentation()
INSTANCE_SEGMENTATION.load_model(os.environ.get('SEGMENTATION_MODEL'))
TARGET_CLASSES = INSTANCE_SEGMENTATION.select_target_classes(person=True)
print('====== Initialized the segmentation server ======')

print('====== Starting the predict server ======')
MODEL = load_model(os.environ.get('POCKET_PARKINSON_MODEL'))
print('====== Initialized the predict server ======')

class SegmentationService:
    name = 'SegmentationService'

    @SQSConsumer('https://sqs.sa-east-1.amazonaws.com/206354660150/pocket-parkinson-segmentation-queue.fifo')
    def handle_message(self, body):
        try:
            print('Segmentation Queue Consume')
            _file_path = create_tmp_image(body['image'])
            _mask, _ = INSTANCE_SEGMENTATION.segmentImage(
                _file_path, 
                segment_target_classes=TARGET_CLASSES, 
                extract_segmented_objects=True, 
                verbose=0
            )

            _mask = _mask['masks'].astype(int)
            _tmp_img = skimage.io.imread(_file_path)

            for i in range(_mask.shape[2]):
                for j in range(_tmp_img.shape[2]):
                    _tmp_img[:,:,j] = _tmp_img[:,:,j] * _mask[:,:,i]

            _, _segmented_img = cv2.threshold(_tmp_img, 0, 255, cv2.THRESH_BINARY)
            cv2.imwrite(_file_path, _segmented_img)
            return json.dumps({
                'status': '200',
                'segmented_img': to_byte_str(_file_path)
            })
        except Exception as e:
            print('Segmentation Queue Consume - Error:', str(e))
            return json.dumps({
                'status': '500',
                'error': str(e)
            })
        finally:
            clear_tmp()

class PredictionService:
    name = 'PredictionService'

    def __init__(self):    

    def _convert_image(self, file_path):
        _image = Image.open(_file_path)
        _image = _image.convert('RGB')
        _image = _image.resize((150,150))
        return np.array([np.asarray(_image)]) / 255.0

    @SQSConsumer('https://sqs.sa-east-1.amazonaws.com/206354660150/pocket-parkinson-prediction-queue.fifo')
    def handle_message(self, body):
        try:
            print('Predict Queue Consume')
            _file_path = create_tmp_image(body['image'])
            _predict = MODEL.predict(self._convert_image(_file_path))[0]
            return json.dumps({
                'status': '200',
                'percentage': {
                    'others': _predict[0],
                    'parkinson': _predict[1]
                }
            })
        except Exception as e:
            print('Predict Queue Consume - Error:', str(e))
            return json.dumps({
                'status': '500',
                'error': str(e)
            })
        finally:
            clear_tmp()