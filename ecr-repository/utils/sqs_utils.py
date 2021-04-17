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

class Consumer(Entrypoint):

    def __init__(self, queue_url, **kwargs):
        self._queue_url = queue_url
        super(Consumer, self).__init__(**kwargs)

    def start(self):
        self.container.spawn_managed_thread(self.run, identifier="Consumer.run")

    def run(self):
        while True:
            _response = SQS_CLIENT.receive_message(
                QueueUrl=self._queue_url,
                WaitTimeSeconds=15,
            )

            for message in _response.get('Messages', ()):
                self._handle_message(message)

    def _handle_message(self, message):
        _handle_result = partial(self._handle_result, message)

        self.container.spawn_worker(
            self, 
            (message['Body'],), 
            {}, 
            handle_result=_handle_result
        )

    def _handle_result(self, message, worker_ctx, result, exc_info):
        SQS_CLIENT.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
        return result, exc_info

SQSConsumer = Consumer.decorator