import json
import os
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder

DYNAMODB_RESOURCE = boto3.resource('dynamodb')
DYNAMODB_CLIENT = boto3.client('dynamodb')
REPORT_TABLE = DYNAMODB_RESOURCE.Table(os.environ['REPORT_TABLE'])

class ReportModel:
    def __init__(self, data):
        self.name = data['name']
        self.active = data['active']
        self.filterExpression = str(data['FilterExpression'])
        self.icon = data['icon']
        self.projectionExpression = str(data['ProjectionExpression'])
        self.tableName = str(data['TableName'])
        self.titles = str(data['titles'])
        self.additional = json.loads(json.dumps(data['additional'])) if 'additional' in data else None

def get_all(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(REPORT_TABLE.scan(
            FilterExpression=Attr('active').eq(1)
        )['Items'], cls=DecimalEncoder)
    }

def get_data(event, context):
    _report = ReportModel(json.loads(event['body'])).__dict__
    _report_data = DYNAMODB_CLIENT.scan(
        FilterExpression=_replace_parameters(_report),
        ProjectionExpression=_report.projectionExpression,
        TableName=_report.tableName
    )
    return {
        'statusCode': 200,
        'body': json.dumps(_report_data['Items'], cls=DecimalEncoder)
    }

def _replace_parameters(report):
    _filterExpression = report.filterExpression

    while '#' in _filterExpression:
        _start = _filterExpression.index('#')
        _end = _filterExpression.index('#', _start + 1) + 1
        _key = _filterExpression[_start:_end]
        _filterExpression =_filterExpression.replace(_key, str(report.additional[_key.replace('#', '')]))

    report.filterExpression = _filterExpression
    return report
