"""
ASGI config for souslik project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/
"""

import os

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.routing import ProtocolTypeRouter
from shadow import hide

from cubicle.auth import AuthMiddlewareStack

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "souslik.settings")

consumers = {}

class Consumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await super().connect()
        consumers[self.scope['user'].username] = self
        await self.send_json(["hey", "you"])


Consumer.send_json = hide(Consumer.send_json)


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(Consumer.as_asgi()),
    "http": get_asgi_application(),
})
