import json
import boto3


LAMBDA_CLIENT = boto3.client('lambda')

def invoke(name, payload, invocation_type='RequestResponse'):
    response = LAMBDA_CLIENT.invoke(
        FunctionName=f'serverless-parkinson-de-bolso-dev-{name}',
        InvocationType=invocation_type,
        Payload=bytes(json.dumps({
            'body': payload
        }), encoding='utf8')
    )

    return json.loads(response['Payload'].read().decode('utf-8'))