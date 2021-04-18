import os
import math
import json
import traceback
import numpy as np
import keras.backend as K
K.set_image_data_format('channels_last')

from PIL import Image
from keras.models import load_model
from utils.db_utils import add_to_table
from utils.file_utils import delete_local_tmp_imagem


class PredictionService:

    def __init__(self):    
        self._service_name = 'PredictionService'
        self._model = load_model(os.environ.get('POCKET_PARKINSON_MODEL'))
        self._predict_table = os.environ.get('PREDICT_TABLE')

    def get_name(self):
        return self._service_name

    def get_queue(self):
        return os.environ.get('PREDICT_QUEUE')
        
    def _inv_softmax(self, x):
        return (K.log(x) + K.log(math.log(10.))).numpy()[0]

    def _convert_output(self, predict_value):
        _converted_values = self._inv_softmax(predict_value)
        _prediction_category = np.argmax(predict_value, axis=1)[0]
        return str(_converted_values[_prediction_category] * 100), int(_prediction_category == 1)

    def _convert_image(self, file_path):
        _image = Image.open(file_path)
        _image = _image.convert('RGB')
        _image = _image.resize((150, 150))
        return np.array([np.asarray(_image)]) / 255.0

    def run(self, body):
        try:
            # converting from string to map
            body = json.loads(body)

            # get the path of the local file
            _file_path = body['local_image']

            # predict the local image
            # 0 - others
            # 1 - parkinson 
            _predict = self._model.predict(self._convert_image(_file_path))

            # remove local temporary image
            delete_local_tmp_imagem(_file_path)

            # convert results
            _porcentage, _isParkinson = self._convert_output(_predict)

            # save data to the database
            add_to_table(self._predict_table, {
                'predictid': body['predictid'],
                'patientid': body['patientid'],
                'index': body['index'],
                'image': body['url_image'],
                'isParkinson': _isParkinson,
                'percentage': _porcentage
            })
            
        except Exception as e:
            print(traceback.format_exc())

        return body
        