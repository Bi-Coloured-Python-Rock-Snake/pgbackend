from channels.generic.websocket import AsyncJsonWebsocketConsumer
from greenhack import exempt

consumers = {}


class Consumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await super().connect()
        consumers[self.scope['user'].username] = self


Consumer.send_json = exempt(Consumer.send_json)
