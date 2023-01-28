from channels.generic.websocket import AsyncJsonWebsocketConsumer
from creature import exempt

consumers = {}


class AsyncJsonWebsocketConsumer(AsyncJsonWebsocketConsumer):
    send_json = exempt(AsyncJsonWebsocketConsumer.send_json)


class Consumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await super().connect()
        consumers[self.scope['user'].username] = self

    async def disconnect(self, code):
        await super().disconnect(code=code)
        consumers.pop(self.scope['user'].username, None)
