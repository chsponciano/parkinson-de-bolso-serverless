import json
import os
import boto3

from util.decimal_encoder import DecimalEncoder

DYNAMODB_RESOURCE = boto3.resource('dynamodb')
CONFIGURATION_APP_TABLE = DYNAMODB_RESOURCE.Table(os.environ['CONFIGURATION_APP_TABLE'])

def get_all(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(CONFIGURATION_APP_TABLE.scan()['Items'], cls=DecimalEncoder)
    }
