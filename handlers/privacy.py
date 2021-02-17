import json
import os

from handlers import patient, patient_classification


def clean_data(event, context):
    _patients = json.loads(patient.get_all(event, context)['body'])
    for p in _patients:
        event['pathParameters']['patientid'] = p['id']
        
        _classification = json.loads(patient_classification.get_all(event, context)['body'])
        for c in _classification:
            event['pathParameters']['id'] = c['id']
            patient_classification.delete(event, context)

        event['pathParameters']['id'] = p['id']
        patient.delete(event, context)
    
    return {
        'statusCode': 200
    }