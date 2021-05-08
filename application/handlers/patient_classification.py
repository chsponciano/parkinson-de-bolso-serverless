import json
import os
import uuid
import boto3
import time
import itertools

from datetime import datetime
from operator import itemgetter
from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder
from util import lambda_utils


DYNAMODB_RESOURCE = boto3.resource('dynamodb')
PATIENT_CLASSIFICATION_TABLE = DYNAMODB_RESOURCE.Table(os.environ['PATIENT_CLASSIFICATION_TABLE'])

class PatientClassificationModel:
    def __init__(self, data):
        self.patientid = data['patientid']
        self.executationid = data['executationid']
        self.percentage = data['percentage']
        self.isParkinson = data['isParkinson']

def group_sort_by_date(stack):
    sorted_stack = sorted(stack, key=itemgetter('date'))
    grouped = []

    for key, values in itertools.groupby(sorted_stack, key=lambda x:x['date']):
        values = list(values)
        element = values[0]
        element['percentage'] = sum(float(g['percentage']) for g in values) / len(values)
        grouped.append(element)

    return grouped

def get_all(event, context):
    _patientsClassifications = PATIENT_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('patientid').eq(event['pathParameters']['patientid'])
    )

    _patientsClassifications = group_sort_by_date(_patientsClassifications['Items'])

    return {
        'statusCode': 200,
        'body': json.dumps(_patientsClassifications, cls=DecimalEncoder)
    }

def delete(event, context):
    _data = json.loads(json.dumps(event['body']))
    _patientid = _data['patientid']

    _patientsClassifications = PATIENT_CLASSIFICATION_TABLE.scan(
        FilterExpression=Attr('patientid').eq(_patientid)
    )

    for classfication in _patientsClassifications['Items']:
        PATIENT_CLASSIFICATION_TABLE.delete_item(
            Key={
                'id': classfication['id']
            }
        )
        
        lambda_utils.invoke('ExecutationDelete', {
            'predictid': classfication['executationid']
        })

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
