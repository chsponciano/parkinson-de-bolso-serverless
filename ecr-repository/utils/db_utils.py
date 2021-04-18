import boto3
import uuid
import time


DYNAMODB = boto3.resource('dynamodb')

def add_to_table(table_name, data):
    _table = DYNAMODB.Table(table_name)
    _timestamp = str(time.time())
    data['id'] = str(uuid.uuid1())
    data['createdAt'] = _timestamp
    data['updatedAt'] = _timestamp
    _table.put_item(Item=data)
