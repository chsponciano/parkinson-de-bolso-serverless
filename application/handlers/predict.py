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
DEFAULT_QUEUE = os.environ['SEGMENTATION_QUEUE_URL']
LAMBDA_CLIENT = boto3.client('lambda')
DEFAULT_NOTIFICATION_TITLE = 'Resultado da analise das imagens'
DEFAULT_NOTIFICATION_MESSAGE = 'Com base nas imagens recebidas, concluímos o paciente tem {percentage:.5f}% de{conclusion} possuir a doença de Parkinson'

def _add_message_to_queue(data):
    _id = uuid.uuid4().hex
    SQS_CLIENT.send_message(
        QueueUrl=DEFAULT_QUEUE,
        MessageBody=json.dumps(data),
        MessageGroupId=_id,
        MessageDeduplicationId=_id
    )

def _get_percentages(predict_id):
    _executations = EXECUTATION_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('predictid').eq(predict_id)
    )['Items']

    _total_amount_records = len(_executations)
    _percentage_parkinson = _percentage_others = 0
    
    if _total_amount_records > 0:
        for executation in _executations:
            if executation['isParkinson'] == 1:
                _percentage_parkinson += int(executation['percentage'])
            else:
                _percentage_others += int(executation['percentage'])

        _percentage_parkinson = int(_percentage_parkinson / _total_amount_records)
        _percentage_others = int(_percentage_others / _total_amount_records)
    
    return _percentage_parkinson, _percentage_others

def create_predict_id(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'predictid': str(uuid.uuid4().hex)
        })
    }

def add_image_prediction_queue(event, context):
    _data = json.loads(event['body'])
    _data['url_image'] = file_control.add(_data['image'], path='dataCollectedTesting/wait/')
    del _data['image']
    _add_message_to_queue(_data)
    return {
        'statusCode': 200,
    }

def request_terminate_prediction(event, context):
    _data = json.loads(event['body'])
    _add_message_to_queue({
        'conclude': _data['predictid'],
        'patiendid': _data['patiendid'],
        'userid': _data['userid'],
    })
    return {
        'statusCode': 200,
    }

def terminate_prediction(event, context):
    _data = json.loads(event['body'])
    _percentage_parkinson, _percentage_others = _get_percentages(_data['predictid'])

    _classification_data = {
        'patientid': _data['patientid'],
        'executationid': _data['predictid'],
    }

    if _percentage_parkinson > _percentage_others:
        _classification_data['percentage'] = _percentage_parkinson
        _classification_data['isParkinson'] = 1
    else:
        _classification_data['percentage'] = _percentage_others
        _classification_data['isParkinson'] = 0

    response = LAMBDA_CLIENT.invoke(
        FunctionName='serverless-parkinson-de-bolso-dev-PatientClassificationCreate',
        InvocationType='RequestResponse',
        Payload=json.dumps(_classification_data)
    )

    _classification = json.loads(response)

    if ('statusCode' in _classification and _classification['statusCode'] == 200):
        _conclusion = '' if _classification['body']['isParkinson'] else ' não'

        _notification_data = {
            'title': DEFAULT_NOTIFICATION_TITLE,
            'body': DEFAULT_NOTIFICATION_MESSAGE.format(
                percentage=_classification['body']['percentage'],
                conclusion=_conclusion
            ),
            'userid': _data['userid'],
            'additional': _classification['body']['executationid'],
            'payload': 'classification'
        }

        LAMBDA_CLIENT.invoke(
            FunctionName='serverless-parkinson-de-bolso-dev-NotificationCreate',
            InvocationType='Event',
            Payload=json.dumps(_notification_data)
        )

        return {
            'statusCode': 200,
            'body': json.dumps(_classification)
        }
    else:
        return {
            'statusCode': 500,
            'error': 'it was not possible to create the final classification'
        }