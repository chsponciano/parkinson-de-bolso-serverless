import os
import json
import boto3


LAMBDA_CLIENT = boto3.client('lambda')
DEFAULT_NAME = os.environ['DEFAULT_NAME_LAMBDA']

def invoke_prediction_termination(predictid, patiendid, userid):
    LAMBDA_CLIENT.invoke(
        FunctionName=f'{DEFAULT_NAME}-TerminatePrediction', 
        InvocationType='Event', 
        Payload=json.dumps({
            'predictid': predictid,
            'patiendid': patiendid,
            'userid': userid,
        })
    )
