import json
import os
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder

DYNAMODB_RESOURCE = boto3.resource('dynamodb')
REPORT_TABLE = DYNAMODB_RESOURCE.Table(os.environ['REPORT_TABLE'])

def get_all(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(REPORT_TABLE.scan(
            FilterExpression=Attr('active').eq(1)
        )['Items'], cls=DecimalEncoder)
    }
