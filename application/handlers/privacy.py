import json
import os
import boto3

from util import lambda_utils

COGNITO_CLIENT = boto3.client('cognito-idp')

def clean_data(event, context):
    _userid = event['pathParameters']['userid']
    lambda_utils.invoke('PatientDeleteAll', {
        'userid': _userid
    })
    return {
        'statusCode': 200
    }

def delete_user(event, context):
    clean_data(event, context)

    COGNITO_CLIENT.admin_delete_user(
        UserPoolId=os.environ['USER_POOL_ID'],
        Username=event['pathParameters']['userid']
    )
    
    return {
        'statusCode': 200
    }