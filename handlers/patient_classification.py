import json
import os
import uuid
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PATIENT_CLASSIFICATION_TABLE'])

class PatientClassificationModel:
    def __init__(self, data):
        self.patientid = data['patientid']
        self.percentage = data['percentage']
        self.date = data['date']
        
def get_all(event, context):
    _patiensClassifications = table.scan(
        FilterExpression=Attr('patientid').eq(event['pathParameters']['patientid'])
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patiensClassifications['Items'], cls=DecimalEncoder)
    }

def delete(event, context):
    table.delete_item(
        Key={
            'id': event['pathParameters']['id']
        }
    )
    return {
        'statusCode': 200
    }

def create(event, context):    
    _patiensClassifications = PatientClassificationModel(json.loads(event['body'])).__dict__
    _patiensClassifications['id'] = str(uuid.uuid1())
    table.put_item(Item=_patiensClassifications)

    return {
        'statusCode': 200,
        'body': json.dumps(_patiensClassifications)
    }