import json
import os
import time
import logging
import uuid
import boto3
import base64

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder
from util import update_parameters

s3 = boto3.resource("s3")
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
        self.image = data['image'] if 'image' in data else None
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
    _patiens = table.scan(
        FilterExpression=Attr('userid').eq(event['pathParameters']['userid'])
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_patiens['Items'], cls=DecimalEncoder)
    }

def _put_file(image_data):
    _filename = str(uuid.uuid1()) + os.path.splitext(image_data['filename'])[1]
    _object = s3.Object(os.environ['BUCKET_NAME'], _filename)
    _object.put(Body=base64.b64decode(image_data['data']))
    _object_acl = s3.ObjectAcl(os.environ['BUCKET_NAME'], _filename)
    _object_acl.put(ACL='public-read')
    return update_parameters.get_s3_url(_filename)

def _delete_file(filename: str):
    filename = filename.split('/')[-1]
    s3.Object(os.environ['BUCKET_NAME'], filename).delete()

def create(event, context):
    _timestamp = str(time.time())
    _data = json.loads(event['body'])
    
    if 'image' in _data and _data['image'] is not None:
        _data['image'] = _put_file(_data['image'])

    _patient = PatientModel(_data).__dict__
    _patient['id'] = str(uuid.uuid1())
    _patient['createdAt'] = _timestamp
    _patient['updatedAt'] = _timestamp

    table.put_item(Item=_patient)
    return {
        'statusCode': 200,
        'body': json.dumps(_patient)
    }

def put(event, context):
    _id = event['pathParameters']['id']
    _item = PatientModel(json.loads(event['body'])).__dict__
    _item['updatedAt'] = str(time.time())

    if 'image' in _item: 
        _old_patient = table.get_item(Key = {'id': _id})['Item']
        if _old_patient['image'] is not None and 'http' in _old_patient['image']:
            _delete_file(_old_patient['image'])
        _item['image'] = _put_file(_item['image'])
    else:
        del _item['image']
    
    _expressions, _attribute_values = update_parameters.get(_item)

    _patient = table.update_item(
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
    
    _old_patient = table.get_item(Key = {'id': _id})['Item']
    if _old_patient['image'] is not None and 'http' in _old_patient['image']:
        _delete_file(_old_patient['image'])

    table.delete_item(
        Key={
            'id': _id
        }
    )
    return {
        'statusCode': 200
    }