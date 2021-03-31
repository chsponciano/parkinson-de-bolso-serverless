import json
import os
import boto3

SENDER = os.environ['APPLICATION_EMAIL']
DEV_EMAIL = os.environ['DEV_EMAIL']
CHARSET = 'UTF-8'

def send_comment(event, context):
    _data = json.loads(event['body'])
    _client = boto3.client('ses')

    try:
        response = _client.send_email(
            Destination={
                'ToAddresses': [
                    DEV_EMAIL,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': _data['comment'],
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': 'Parkinson de Bolso - Comentário de usuário',
                },
            },
            Source=SENDER,
        )

        return {
            'statusCode': 200,
            'response': str(response)
        }
    except Exception as e:
        return {
            'statusCode': 502,
            'error': str(e)
        }
