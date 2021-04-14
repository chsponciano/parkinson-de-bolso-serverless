import os

from dotenv import load_dotenv
load_dotenv()

from file_utils import clear_tmp, create_tmp_image, to_byte_str
from sqs_utils import SQSConsumer

from pixellib.instance import instance_segmentation
import skimage.io
import cv2

class SegmentationService:
    name = os.environ.get('SEGMENTATION_SERVICE')

    def __init__(self):    
        self._segmentation = instance_segmentation()
        self._segmentation.load_model(os.path.join(os.getcwd(), os.environ.get('SEGMENTATION_MODEL')))
        self._target_classes = self._segmentation.select_target_classes(person=True)

    @SQSConsumer(os.environ.get('SEGMENTATION_QUEUE'))
    def handle_message(self, body):
        try:
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


from keras.models import load_model
from PIL import Image

class PredictionService:
    name = os.environ.get('PREDICTION_SERVICE')

    def __init__(self):    
        self._model = load_model(os.path.join(os.getcwd(), os.environ.get('POCKET_PARKINSON_MODEL')))

    def _convert_image(self, file_path):
        _image = Image.open(_file_path)
        _image = _image.convert('RGB')
        _image = _image.resize((150,150))
        return np.array([np.asarray(_image)]) / 255.0

    @SQSConsumer(os.environ.get('PREDICTION_QUEUE'))
    def handle_message(self, body):
        try:
            _file_path = create_tmp_image(body['image'])
            _predict = _model.predict(self._convert_image(_file_path))[0]
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