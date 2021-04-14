import json
import os

from handlers import patient, patient_classification


def clean_data(event, context):
    _patients = json.loads(patient.get_all(event, context)['body'])
    for _patient in _patients:
        event['pathParameters']['patientid'] = _patient['id']
        
        _classifications = json.loads(patient_classification.get_all(event, context)['body'])
        for _classification in _classifications:
            event['pathParameters']['id'] = _classification['id']
            patient_classification.delete(event, context)

        event['pathParameters']['id'] = _patient['id']
        patient.delete(event, context)
    
    return {
        'statusCode': 200
    }