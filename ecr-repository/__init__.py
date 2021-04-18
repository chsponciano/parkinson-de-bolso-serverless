import os

from dotenv import load_dotenv
load_dotenv()

from services.prediction_service import PredictionService
from services.segmentation_service import SegmentationService
from utils.sqs_utils import SQSConsume

if __name__ == '__main__':
    for service in [SegmentationService(), PredictionService()]:
        consume = SQSConsume(
            service.get_name(), 
            os.environ.get('SEQMENTATION_QUEUE'), 
            os.environ.get('AWS_REGION'), 
            service.run
        )
        consume.start()
