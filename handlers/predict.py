import json
import os
import time
import uuid
import base64
import random
import boto3

from boto3.dynamodb.conditions import Attr


dynamodb = boto3.resource('dynamodb')
executation_classification_table = dynamodb.Table(os.environ['EXECUTATION_CLASSIFICATION_TABLE'])

def evaluator(event, context):
    _timestamp = str(time.time())
    _executation = json.loads(event['body'])
    _executation['id'] = str(uuid.uuid1())
    _executation['createdAt'] = _timestamp
    _executation['updatedAt'] = _timestamp

    # start of implementation
    _executation_image = base64.b64decode(_executation['image']['data'])
    del _executation['image']

    # temporary random value until model creation
    _executation['percentage'] = str(random.randint(0, 100))

    executation_classification_table.put_item(Item=_executation)
    return {
        'statusCode': 200,
        'body': json.dumps(_executation)
    }

def conclude(event, context):
    _id = event['pathParameters']['patientid']
    _executations = executation_classification_table.scan(
        FilterExpression=Attr('patientid').eq(_id)
    )['Items']

    _list_size = len(_executations)
    _sum_percentages = 0

    for e in _executations:
        _sum_percentages += int(e['percentage'])
        executation_classification_table.delete_item(Key={ 'id': e['id'] })

    _sum_percentages = int(_sum_percentages / _list_size)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'percentage': str(_sum_percentages)
        })
    }
