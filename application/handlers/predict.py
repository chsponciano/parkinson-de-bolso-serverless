import json
import os
import time
import uuid
import random
import boto3

from boto3.dynamodb.conditions import Attr
from util import file_control, lambda_utils
from util.decimal_encoder import DecimalEncoder

EC2_CLIENT = boto3.client('ec2')
SQS_CLIENT = boto3.client('sqs')
DYNAMODB_RESOURCE = boto3.resource('dynamodb')
EXECUTATION_CLASSIFICATION_TABLE = DYNAMODB_RESOURCE.Table(os.environ['EXECUTATION_CLASSIFICATION_TABLE'])
DEFAULT_QUEUE = os.environ['SEGMENTATION_QUEUE_URL']
DEFAULT_NOTIFICATION_TITLE = 'Resultado da analise das imagens'
DEFAULT_NOTIFICATION_MESSAGE = 'Com base nas imagens recebidas, concluímos que o paciente {patient} tem {percentage:.5f}% de{conclusion} possuir a doença de Parkinson'
DEFAULT_NOTIFICATION_MESSAGE_NO_RESULTS = 'Com base nas imagens recebidas, não identificamos o paciente {patient} nas imagens! Favor repetir o procedimento.'

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
                _percentage_parkinson += float(executation['percentage'])
            else:
                _percentage_others += float(executation['percentage'])

        _percentage_parkinson = _percentage_parkinson / _total_amount_records
        _percentage_others = _percentage_others / _total_amount_records
    
    return _percentage_parkinson, _percentage_others

def get_all_by_id(event, context):
    _executationClassifications = EXECUTATION_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('predictid').eq(event['pathParameters']['id'])
    )

    return {
        'statusCode': 200,
        'body': json.dumps(_executationClassifications['Items'], cls=DecimalEncoder)
    }

def delete_data(event, context):
    _data = json.loads(json.dumps(event['body']))
    _predictid = _data['predictid']

    _executationClassifications = EXECUTATION_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('predictid').eq(_predictid)
    )

    for executation in _executationClassifications['Items']:
        EXECUTATION_CLASSIFICATION_TABLE.delete_item(
            Key={
                'id': executation['id']
            }
        )

    return {
        'statusCode': 200
    }

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
        'patientid': _data['patientid'],
        'userid': _data['userid'],
    })
    return {
        'statusCode': 200,
    }

def terminate_prediction(event, context):
    _data = json.loads(json.dumps(event['body']))
    _id = _data['predictid']

    _percentage_parkinson, _percentage_others = _get_percentages(_id)

    _patientName = lambda_utils.invoke('PatientGetName', {
        'patientid': _data['patientid'],
    })

    if _percentage_parkinson == _percentage_others == 0:
        _notification_data = {
            'title': DEFAULT_NOTIFICATION_TITLE,
            'body': DEFAULT_NOTIFICATION_MESSAGE_NO_RESULTS.format(
                patient=_patientName
            ),
            'userid': _data['userid'],
            'additional': None,
            'payload': 'alert'
        }

        lambda_utils.invoke('NotificationCreate', _notification_data)

    else:
        _percentage, _is_parkinson = (_percentage_parkinson, 1) if _percentage_parkinson > _percentage_others else (_percentage_others, 0)

        _classification = lambda_utils.invoke('PatientClassificationCreate', {
            'patientid': _data['patientid'],
            'executationid': _id,
            'percentage': str(_percentage),
            'isParkinson': _is_parkinson
        })

        if ('statusCode' in _classification and _classification['statusCode'] == 200):
            _conclusion = '' if _is_parkinson else ' não'

            _notification_data = {
                'title': DEFAULT_NOTIFICATION_TITLE,
                'body': DEFAULT_NOTIFICATION_MESSAGE.format(
                    patient=_patientName,
                    percentage=_percentage,
                    conclusion=_conclusion
                ),
                'userid': _data['userid'],
                'additional': _id,
                'payload': 'classification'
            }

            lambda_utils.invoke('NotificationCreate', _notification_data)
        else:
            return {
                'statusCode': 500,
                'error': 'it was not possible to create the final classification'
            }
            
    return {
        'statusCode': 200
    }

def machine_status(event, context):
    _instances = EC2_CLIENT.describe_instance_status(IncludeAllInstances=True)
    _active = 1

    for instance in _instances['InstanceStatuses']:
        _active = 1 if instance['InstanceState']['Code'] == 16 and _active == 1 else 0

    return {
        'statusCode': 200,
        'body': json.dumps({
            'active': _active
        })
    }