import os
import json
import time
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

    response = json.loads(response['Payload'].read().decode('utf-8'))
    print('[%s] Invoke prediction termination - Response: %s' % (time.ctime(time.time()), response))
    return response
