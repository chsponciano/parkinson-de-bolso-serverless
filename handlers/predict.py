import json
import os
import boto3


dynamodb = boto3.resource('dynamodb')
active_classification_table = dynamodb.Table(os.environ['ACTIVE_CLASSIFICATION_TABLE'])
executation_classification_table = dynamodb.Table(os.environ['EXECUTATION_CLASSIFICATION_TABLE'])

def initialize(event, context):
    return {
        'statusCode': 200,
    }

def evaluator(event, context):
    return {
        'statusCode': 200,
    }

def conclude(event, context):
    return {
        'statusCode': 200,
    }
