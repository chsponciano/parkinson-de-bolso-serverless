import json
import os
import keras


def predict(event, context):
    return {
        'statusCode': 200,
        'body': 'keras'
    }