
import os

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.routing import ProtocolTypeRouter
from greenhack import exempt


from django.core.asgi import get_asgi_application

from auth_middleware import AuthMiddlewareStack

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")

consumers = {}


class Consumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await super().connect()
        consumers[self.scope['user'].username] = self


Consumer.send_json = exempt(Consumer.send_json)


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(Consumer.as_asgi()),
    "http": get_asgi_application(),
})
