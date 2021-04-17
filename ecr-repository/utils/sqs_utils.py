import boto3
import json
import uuid
import os

from nameko.extensions import Entrypoint
from functools import partial


AWS_REGION = os.environ.get('AWS_REGION')
SQS_CLIENT = boto3.client('sqs', region_name=AWS_REGION)

def SQSProducer(queue_url, message):
    _id = uuid.uuid4().hex

    return SQS_CLIENT.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message),
        MessageGroupId=_id,
        MessageDeduplicationId=_id
    )

class Receive(Entrypoint):

    def __init__(self, queue_url, region="sa-east-1", **kwargs):
        self.url = queue_url
        self.region = os.environ.get('AWS_REGION')
        super(Receive, self).__init__(**kwargs)

    def setup(self):
        self.client = boto3.client('sqs', region_name=self.region)

    def start(self):
        self.container.spawn_managed_thread(
            self.run, identifier="Receive.run"
        )

    def run(self):
        while True:
            response = self.client.receive_message(
                QueueUrl=self.url,
                WaitTimeSeconds=5,
            )
            messages = response.get('Messages', ())
            for message in messages:
                self.handle_message(message)

    def handle_message(self, message):
        handle_result = partial(self.handle_result, message)

        args = (message['Body'],)
        kwargs = {}

        self.container.spawn_worker(
            self, args, kwargs, handle_result=handle_result
        )

    def handle_result(self, message, worker_ctx, result, exc_info):
        # assumes boto client is thread-safe for this action, because it
        # happens inside the worker threads
        self.client.delete_message(
            QueueUrl=self.url,
            ReceiptHandle=message['ReceiptHandle']
        )
        return result, exc_info

SQSConsumer = Receive.decorator