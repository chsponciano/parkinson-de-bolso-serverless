import json
import os
import time
import uuid
import random
import boto3

from boto3.dynamodb.conditions import Attr
from util import file_control


SQS_CLIENT = boto3.client('sqs')
DYNAMODB_RESOURCE = boto3.resource('dynamodb')
EXECUTATION_CLASSIFICATION_TABLE = DYNAMODB_RESOURCE.Table(os.environ['EXECUTATION_CLASSIFICATION_TABLE'])

def _get_percentages(predict_id):
    _executations = EXECUTATION_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('predictid').eq(predict_id)
    )['Items']

    _record_amount = len(_executations)
    _percentage_othres = 0
    _percentage_parkinson = 0

    for e in _executations:
        _percentage_othres += int(e['percentage_others'])
        _percentage_parkinson += int(e['percentage_parkinson'])

    return int(_percentage_othres / _record_amount), int(_percentage_parkinson / _record_amount)

def create_predict_id(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'predictid': str(uuid.uuid4().hex)
        })
    }

def evaluator(event, context):
    _id = uuid.uuid4().hex
    _data = json.loads(event['body'])
    _data['url_image'] = file_control.add(_data['image'], path='dataCollectedTesting/wait/')
    del _data['image']

    SQS_CLIENT.send_message(
        QueueUrl=os.environ['SEGMENTATION_QUEUE_URL'],
        MessageBody=json.dumps(_data),
        MessageGroupId=_id,
        MessageDeduplicationId=_id
    )

    response = {}

    if int(_data['index']) > 0:
        response['percentage_othres'], response['percentage_parkinson'] = _get_percentages(_data['predictid'])

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }

def conclude(event, context):
    _percentage_othres, _percentage_parkinson = _get_percentages(_data['predictid'])

    return {
        'statusCode': 200,
        'body': json.dumps({
            'percentages': {
                'othres': _percentage_othres,
                'parkinson': _percentage_parkinson
            } 
        })
    }
