from channels.generic.websocket import AsyncJsonWebsocketConsumer
from greenhack import exempt

consumers = {}


class Consumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await super().connect()
        consumers[self.scope['user'].username] = self

    async def disconnect(self, code):
        await super().disconnect(code=code)
        consumers.pop(self.scope['user'].username, None)

Consumer.send_json = exempt(Consumer.send_json)
