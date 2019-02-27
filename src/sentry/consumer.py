from __future__ import absolute_import, print_function

from batching_kafka_consumer import AbstractBatchWorker

from django.conf import settings

import sentry.tasks.store as store_tasks
from sentry.utils import json


def handle_preprocess(message):
    data = message['data']
    event_id = data['event_id']
    cache_key = message['attachments_cache_key']
    start_time = message['start_time']
    process_task = (
        store_tasks.process_event_from_reprocessing
        if message['from_reprocessing']
        else store_tasks.process_event
    )

    store_tasks._do_preprocess_event(cache_key, data, start_time, event_id, process_task)


def handle_process(message):
    data = message['data']
    event_id = data['event_id']
    cache_key = message['attachments_cache_key']
    start_time = message['start_time']
    process_task = (
        store_tasks.process_event_from_reprocessing
        if message['from_reprocessing']
        else store_tasks.process_event
    )

    store_tasks._do_process_event(cache_key, start_time, event_id, process_task, data=data)


def handle_save(message):
    data = message['data']
    event_id = data['event_id']
    cache_key = message['attachments_cache_key']
    start_time = message['start_time']
    project_id = data['project']

    store_tasks._do_save_event(cache_key, data, start_time, event_id, project_id)


class ConsumerWorker(AbstractBatchWorker):
    def __init__(self):
        self.dispatch = {}
        for key, handler in (
            (settings.KAFKA_PREPROCESS, handle_preprocess),
            (settings.KAFKA_PROCESS, handle_process),
            (settings.KAFKA_SAVE, handle_save)
        ):
            topic = settings.KAFKA_TOPICS[key]['topic']
            self.dispatch[topic] = handler

    def process_message(self, message):
        topic = message.topic()
        return self._handle(topic, json.loads(message.value()))

    def _handle(self, topic, message):
        handler = self.dispatch[topic]
        return handler(message)

    def flush_batch(self, batch):
        pass

    def shutdown(self):
        pass
