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

class SegmentationService:
    name = 'SegmentationService'

    def __init__(self):    
        print('Starting the segmentation server')
        _path_model = os.environ.get('SEGMENTATION_MODEL')
        print(f'Model: {_path_model}')
        self._segmentation = instance_segmentation()
        self._segmentation.load_model(_path_model)
        self._target_classes = self._segmentation.select_target_classes(person=True)
        print('Initialized the segmentation server')

    @SQSConsumer('https://sqs.sa-east-1.amazonaws.com/206354660150/pocket-parkinson-segmentation-queue.fifo')
    def handle_message(self, body):
        try:
            print(body)
            _file_path = create_tmp_image(body['image'])
            _mask, _ = self._segmentation.segmentImage(
                _file_path, 
                segment_target_classes=self._target_classes, 
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
            return json.dumps({
                'status': '500',
                'error': str(e)
            })
        finally:
            clear_tmp()

class PredictionService:
    name = 'PredictionService'

    def __init__(self):    
        print('Starting the predict server')
        self._model = load_model(os.path.join(os.getcwd(), os.environ.get('POCKET_PARKINSON_MODEL')))
        print('Initialized the predict server')

    def _convert_image(self, file_path):
        _image = Image.open(_file_path)
        _image = _image.convert('RGB')
        _image = _image.resize((150,150))
        return np.array([np.asarray(_image)]) / 255.0

    @SQSConsumer('https://sqs.sa-east-1.amazonaws.com/206354660150/pocket-parkinson-prediction-queue.fifo')
    def handle_message(self, body):
        try:
            print(body)
            _file_path = create_tmp_image(body['image'])
            _predict = self._model.predict(self._convert_image(_file_path))[0]
            return json.dumps({
                'status': '200',
                'percentage': {
                    'others': _predict[0],
                    'parkinson': _predict[1]
                }
            })
        except Exception as e:
            return json.dumps({
                'status': '500',
                'error': str(e)
            })
        finally:
            clear_tmp()