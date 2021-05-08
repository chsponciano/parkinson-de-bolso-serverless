import json
import os
import time
import uuid
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder
from util import update_parameters, file_control, lambda_utils
from handlers import patient_classification

DYNAMODB_RESOURCE = boto3.resource('dynamodb')
PATIENT_TABLE = DYNAMODB_RESOURCE.Table(os.environ['PATIENT_TABLE'])

class PatientModel:
    def __init__(self, data):
        self.fullname = data['fullname']
        self.birthdate = data['birthdate']
        self.diagnosis = data['diagnosis']
        self.weight = data['weight']
        self.height = data['height']
        self.image = data['image'] if 'image' in data else None
        self.userid = data['userid']

def get(event, context):
    _patient = PATIENT_TABLE.get_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patient['Item'], cls=DecimalEncoder)
    }

def get_all(event, context):
    _patiens = PATIENT_TABLE.scan(
        FilterExpression=Attr('userid').eq(event['pathParameters']['userid'])
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patiens['Items'], cls=DecimalEncoder)
    }

def get_patient_name(event, context):
    _data = json.loads(json.dumps(event['body']))
    _patientid = _data['patientid']

    _patient = PATIENT_TABLE.get_item(
        Key={
            'id': _patientid
        }
    )

    return  _patient['Item']['fullname']

def create(event, context):
    _timestamp = str(time.time())
    _patient = PatientModel(json.loads(event['body'])).__dict__
    _patient['id'] = str(uuid.uuid1())
    _patient['createdAt'] = _timestamp
    _patient['updatedAt'] = _timestamp

    if _patient['image'] is not None:
        _patient['image'] = file_control.add(_patient['image'])

    PATIENT_TABLE.put_item(Item=_patient)
    return {
        'statusCode': 200,
        'body': json.dumps(_patient)
    }

def put(event, context):
    _id = event['pathParameters']['id']
    _patient = PatientModel(json.loads(event['body'])).__dict__
    _patient['updatedAt'] = str(time.time())

    if _patient['image'] is not None and 'http' not in _patient['image']:
        _delete_patient_file(_id)
        _patient['image'] = file_control.add(_patient['image'])
    
    _expressions, _attribute_values = update_parameters.get(_patient)

    _patient = PATIENT_TABLE.update_item(
        Key={
            'id': _id
        },
        UpdateExpression = _expressions,
        ExpressionAttributeValues = _attribute_values,
        ReturnValues='UPDATED_NEW',
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patient['Attributes'], cls=DecimalEncoder)
    }

def delete(event, context):
    _id = event['pathParameters']['id']
    _delete_patient_file(_id)
    
    PATIENT_TABLE.delete_item(
        Key={
            'id': _id
        }
    )
    
    lambda_utils.invoke('PatientClassificationDelete', {
        'patientid': _id
    })
    return {
        'statusCode': 200
    }

def delete_all(event, context):
    _data = json.loads(json.dumps(event['body']))
    _userid = _data['userid']

    _patiens = PATIENT_TABLE.scan(
        FilterExpression=Attr('userid').eq(_userid)
    )

    for patient in _patiens['Items']:
        PATIENT_TABLE.delete_item(
            Key={
                'id': patient['id']
            }
        )
        
        lambda_utils.invoke('PatientClassificationDelete', {
            'patientid': patient['id']
        })

    return {
        'statusCode': 200
    }

def _delete_patient_file(patient_id):
    _patient = PATIENT_TABLE.get_item(Key = {'id': patient_id})['Item']
    if _patient['image'] is not None:
        file_control.delete(_patient['image'])