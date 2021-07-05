import json
import time

import gevent
import locust
from websocket import create_connection


class ChannelTaskSet(locust.TaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.ws = create_connection('ws://localhost:22222/channel')
        self.channel_id = ""

    def on_start(self):
        def _receive():
            while True:
                try:
                    res = self.ws.recv()
                    data = json.loads(res)

                    if data["payloadType"] == "START_TEST":
                        self.channel_id = data["receiver"]
                    elif data["payloadType"] == "BROADCAST":
                        locust.events.request_success.fire(
                            request_type='recv',
                            name='recv',
                            response_time=round(time.time() * 1000) - int(data['regTime']),
                            response_length=len(res),
                        )
                except Exception as e:
                    locust.events.request_failure.fire(
                        request_type='send',
                        name='send',
                        response_time=round(time.time() * 1000),
                        exception=e
                    )

        gevent.spawn(_receive)

    def on_quit(self):
        self.ws.close()

    @locust.task
    def send(self):
        if self.channel_id != "":
            try:
                data = {
                    "payloadType": 4,
                    "receiveType": 1,
                    "receiver": self.channel_id,
                    "regTime": round(time.time() * 1000),
                    "body": "Welcome to the website. If you're here, you're likely looking to find random words. Random Word Generator is the perfect tool to help you do this. While this tool isn't a word creator, it is a word generator that will generate random words for a variety of activities or uses. Even better, it allows you to adjust the parameters of the random words to best fit your needs."
                }
                body = json.dumps(data)
                self.ws.send(body)
                locust.events.request_success.fire(
                    request_type='send',
                    name='send',
                    response_time=round(time.time() * 1000) - int(data['regTime']),
                    response_length=len(data['body']),
                )
            except Exception as e:
                locust.events.request_failure.fire(
                    request_type='send',
                    name='send',
                    response_time=round(time.time() * 1000),
                    exception=e
                )


class ChatLocust(locust.HttpUser):
    tasks = [ChannelTaskSet]
    locust.between(2,10)