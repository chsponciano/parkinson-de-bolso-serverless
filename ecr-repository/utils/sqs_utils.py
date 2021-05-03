import os
import boto3
import json
import uuid
import time
import threading

class SQSProducer:

    def __init__(self, queue_url, region):
        self._queue_url = queue_url
        self._region = region
        self.setup()

    def setup(self):
        self._sqs_client = boto3.client('sqs')

    def run(self, message):
        _id = uuid.uuid4().hex
        _situation = self._sqs_client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(message),
            MessageGroupId=_id,
            MessageDeduplicationId=_id
        )
        print('[%s][%s] message posting - Situation: %s | Queue: %s' % (time.ctime(time.time()), _id, _situation, self._queue_url))

        

class SQSConsume(threading.Thread):
    
    def __init__(self, service_name, queue_url, region, action, sleeping_time=0.5):
        self._service_name = service_name
        self._queue_url = queue_url
        self._region = region
        self._action = action
        self._sleeping_time = sleeping_time
        threading.Thread.__init__(self)
        self.setup()
        print('[%s][%s][%s] initialize aws queue consumer - queue: %s' % (self._service_name, self._name, time.ctime(time.time()), queue_url))

    def setup(self):
        self._sqs_client = boto3.client('sqs', region_name=self._region)

    def restart(self):
        print('[%s][%s][%s] calling a new instance' % (self._service_name, self._name, time.ctime(time.time())))
        consume = SQSConsume(self._service_name, self._queue_url, self._region, self._action)
        consume.start()

    def consume_message_queue(self, message):
        print('[%s][%s][%s] consume message queue' % (self._service_name, self._name, time.ctime(time.time())))
        self._sqs_client.delete_message(
            QueueUrl=self._queue_url, 
            ReceiptHandle=message['ReceiptHandle']
        )

    def handle_message(self, message):
        print('[%s][%s][%s] processing received message' % (self._service_name, self._name, time.ctime(time.time())))
        print('[%s][%s][%s] message received: %s' % (self._service_name, self._name, time.ctime(time.time()), message['Body']))
        self.consume_message_queue(message)
        # self.restart()

        # performs the service action
        self._action(message['Body'])

    def run(self):
        _stop = False

        while(not _stop):
            try:
                print('[%s][%s][%s] looking for new messages...' % (self._service_name, self._name, time.ctime(time.time())))
                
                response = self._sqs_client.receive_message(
                    QueueUrl=self._queue_url, 
                    WaitTimeSeconds=5
                ).get('Messages', ())

                # _stop = len(response) > 0
                    
                for message in response:
                    self.handle_message(message)

                print('[%s][%s][%s] ending search and entering standby' % (self._service_name, self._name, time.ctime(time.time())))
                time.sleep(self._sleeping_time)
            except Exception as e:
                print('[%s][%s][%s] an error has occurred: %s \n' % (self._service_name, self._name, time.ctime(time.time()), str(e)))

        print('[%s][%s][%s] process closure' % (self._service_name, self._name, time.ctime(time.time())))
