import json
import os
import uuid
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder


DYNAMODB_RESOURCE = boto3.resource('dynamodb')
PATIENT_CLASSIFICATION_TABLE = DYNAMODB_RESOURCE.Table(os.environ['PATIENT_CLASSIFICATION_TABLE'])

class PatientClassificationModel:
    def __init__(self, data):
        self.patientid = data['patientid']
        self.percentage = data['percentage']
        self.date = data['date']
        
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
    _patientsClassifications = PatientClassificationModel(json.loads(event['body'])).__dict__
    _patientsClassifications['id'] = str(uuid.uuid1())
    _patientsClassifications['percentage'] = _group_daily_data(_patientsClassifications)
    PATIENT_CLASSIFICATION_TABLE.put_item(Item=_patientsClassifications)

    return {
        'statusCode': 200,
        'body': json.dumps(_patientsClassifications)
    }

def _group_daily_data(patientsClassification):
    _percentage = float(patientsClassification['percentage'])
    _classifications = PATIENT_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('patientid').eq(patientsClassification['patientid']) & Attr('date').eq(patientsClassification['date'])
    )['Items']

    if len(_classifications) == 0:
        return int(_percentage)
    
    for c in _classifications:
        _percentage += float(c['percentage'])
        PATIENT_CLASSIFICATION_TABLE.delete_item(
            Key={
                'id': c['id']
            }
        )

    _percentage /= len(_classifications) + 1

    return int(_percentage)
