import json
import os
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PATIENT_CLASSIFICATION_TABLE'])

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