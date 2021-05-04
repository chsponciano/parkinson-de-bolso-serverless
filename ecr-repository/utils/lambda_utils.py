import os
import json
import boto3


LAMBDA_CLIENT = boto3.client('lambda')
DEFAULT_NAME = os.environ['DEFAULT_NAME_LAMBDA']

def invoke_prediction_termination(data, invocation_type='RequestResponse'):
    data['predictid'] = data['conclude']
    del data['conclude']

    response = LAMBDA_CLIENT.invoke(
        FunctionName=f'{DEFAULT_NAME}-TerminatePrediction', 
        InvocationType=invocation_type, 
        Payload=bytes(json.dumps({
            'body': data
        }), encoding='utf8')
    )

    return json.loads(response['Payload'].read().decode('utf-8'))
