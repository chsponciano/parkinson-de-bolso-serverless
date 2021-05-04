import json
import os
import uuid
import boto3
import time

from datetime import datetime
from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder


DYNAMODB_RESOURCE = boto3.resource('dynamodb')
PATIENT_CLASSIFICATION_TABLE = DYNAMODB_RESOURCE.Table(os.environ['PATIENT_CLASSIFICATION_TABLE'])

class PatientClassificationModel:
    def __init__(self, data):
        self.patientid = data['patientid']
        self.executationid = data['executationid']
        self.percentage = data['percentage']
        self.isParkinson = data['isParkinson']
        
def get_all(event, context):
    _patientsClassifications = PATIENT_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('patientid').eq(event['pathParameters']['patientid'])
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patientsClassifications['Items'], cls=DecimalEncoder)
    }

def delete(event, context):
    PATIENT_CLASSIFICATION_TABLE.delete_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )
    return {
        'statusCode': 200
    }

def create(event, context):  
    _timestamp = str(time.time())  
    _patientsClassifications = PatientClassificationModel(json.loads(json.dumps(event['body']))).__dict__
    _patientsClassifications['id'] = str(uuid.uuid1())
    _patientsClassifications['date'] = str(datetime.date(datetime.now()))
    _patientsClassifications['createdAt'] = _timestamp
    _patientsClassifications['updatedAt'] = _timestamp

    PATIENT_CLASSIFICATION_TABLE.put_item(Item=_patientsClassifications)

    return {
        'statusCode': 200,
        'body': json.dumps(_patientsClassifications)
    }
