import json
import os
import time
import logging
import uuid
import boto3

from util.decimal_encoder import DecimalEncoder
from util import update_parameters


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PATIENT_TABLE'])

class PatientModel:
    def __init__(self, data):
        self.fullname = data['fullname']
        self.birthdate = data['birthdate']
        self.diagnosis = data['diagnosis']
        self.weight = data['weight']
        self.height = data['height']
        self.initials = data['initials']
        self.image = data['image']
        self.userid = data['userid']

def get(event, context):
    _patient = table.get_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patient['Item'], cls=DecimalEncoder)
    }

def get_all(event, context):
    _patiens = table.scan()
    return {
        'statusCode': 200,
        'body': json.dumps(_patiens['Items'], cls=DecimalEncoder)
    }

def create(event, context):
    try:
        _timestamp = str(time.time())
        _patient = PatientModel(json.loads(event['body'])).__dict__
        _patient['id'] = str(uuid.uuid1())
        _patient['createdAt'] = _timestamp
        _patient['updatedAt'] = _timestamp

        table.put_item(Item=_patient)
        return {
            'statusCode': 200,
            'body': json.dumps(_patient)
        }
    except Exception as ex:
        logging.error(f'Error Patient Insertion, error: {ex}')
        raise Exception(f'Error Patient Insertion, error: {ex}')

def put(event, context):
    try:
        _item = PatientModel(json.loads(event['body'])).__dict__
        _item['updatedAt'] = str(time.time())

        _expressions, _attribute_values = update_parameters.get(_item)

        _patient = table.update_item(
            Key={
                'id': event['pathParameters']['id']
            },
            UpdateExpression = _expressions,
            ExpressionAttributeValues = _attribute_values,
            ReturnValues='UPDATED_NEW',
        )
        return {
            'statusCode': 200,
            'body': json.dumps(_patient['Attributes'], cls=DecimalEncoder)
        }
    except Exception as ex:
        logging.error(f'Error Patient Update, error: {ex}')
        raise Exception(f'Error Patient Update, error: {ex}')

def delete(event, context):
    table.delete_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )
    return {
        'statusCode': 200
    }