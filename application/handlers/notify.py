import json
import os
import time
import uuid
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder
from util import update_parameters

SENDER = os.environ['APPLICATION_EMAIL']
DEV_EMAIL = os.environ['DEV_EMAIL']
CHARSET = 'UTF-8'
SES_CLIENT = boto3.client('ses')
DYNAMODB_RESOURCE = boto3.resource('dynamodb')
NOTIFICATION_TABLE = DYNAMODB_RESOURCE.Table(os.environ['NOTIFICATION_TABLE'])

class NotificationModel:
    def __init__(self, data):
        self.title = data['title']
        self.body = data['body']
        self.userid = data['userid']
        self.notificationid = data['notificationid'] if 'notificationid' in data else 0
        self.payload = data['payload'] if 'payload' in data else ''
        self.isread = data['isread'] if 'isread' in data else 0
        self.additional = data['additional'] if 'additional' in data else None

def get_all(event, context):
    _notifications = NOTIFICATION_TABLE.scan(
        FilterExpression=Attr('userid').eq(event['pathParameters']['userid']) & Attr('isread').eq(0)
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_notifications['Items'], cls=DecimalEncoder)
    }

def create(event, context):
    _timestamp = str(time.time())
    _notification = NotificationModel(json.loads(json.dumps(event['body']))).__dict__
    _notification['id'] = str(uuid.uuid1())
    _notification['notificationid'] = int(round(time.time() * 1000))
    _notification['createdAt'] = _timestamp
    _notification['updatedAt'] = _timestamp

    NOTIFICATION_TABLE.put_item(Item=_notification)

    return {
        'statusCode': 200,
        'body': json.dumps(_notification)
    }

def mark_read(event, context):
    _id = event['pathParameters']['id']
    _notification = NotificationModel(json.loads(event['body'])).__dict__
    _notification['updatedAt'] = str(time.time())
    _notification['isread'] = 1
    _expressions, _attribute_values = update_parameters.get(_notification)

    _notification = NOTIFICATION_TABLE.update_item(
        Key={
            'id': _id
        },
        UpdateExpression = _expressions,
        ExpressionAttributeValues = _attribute_values,
        ReturnValues='UPDATED_NEW',
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_notification['Attributes'], cls=DecimalEncoder)
    }

def send_comment(event, context):
    try:
        _data = json.loads(event['body'])
        response = _send_email('Parkinson de Bolso - Comentário de usuário', _data['comment'])
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': response
            })
        }
    except Exception as e:
        return {
            'statusCode': 502,
            'error': str(e)
        }

def new_user(event, context):
    try:
        _data = json.loads(json.dumps(event['body']))
        _message = 'ID: ' + _data['userName'] + '\n'
        _message += 'Nome: ' + _data['request']['userAttributes']['name'] + '\n'
        _message += 'Email: ' + _data['request']['userAttributes']['email']

        response = _send_email('Parkinson de Bolso - Novo usuário', _message)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': response
            })
        }
    except Exception as e:
        return {
            'statusCode': 502,
            'error': str(e)
        }

def _send_email(subject, message):
    return SES_CLIENT.send_email(
        Destination={
            'ToAddresses': [
                DEV_EMAIL,
            ],
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': CHARSET,
                    'Data': message,
                },
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': subject,
            },
        },
        Source=SENDER,
    )