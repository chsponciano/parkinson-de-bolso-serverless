import json
import os
import boto3

from boto3.dynamodb.conditions import Attr
from util.decimal_encoder import DecimalEncoder
from util.lambda_utils import invoke

DYNAMODB_RESOURCE = boto3.resource('dynamodb')
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
        self.userid = data['userid']

def get_all(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(REPORT_TABLE.scan(
            FilterExpression=Attr('active').eq(1)
        )['Items'], cls=DecimalEncoder)
    }

def get_data(event, context):
    _report = ReportModel(json.loads(event['body']))
    
    _report_data = DYNAMODB_RESOURCE.Table(_report.tableName).scan(
        FilterExpression=Attr(_report.filterExpression).eq(_report.additional[_report.filterExpression]),
        ProjectionExpression=_report.projectionExpression
    )

    return invoke('GeneratePdf', {
        'userid': _report.userid,
        'title': _report.name,
        'items': _report_data['Items']
    })
        
