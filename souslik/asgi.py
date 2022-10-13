"""
ASGI config for souslik project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/
"""

import os

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.routing import URLRouter

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.asgi import get_asgi_application
from django.urls import path, re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "souslik.settings")


class Consumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await super().connect()
        await self.send_json(["hey", "you"])


application = URLRouter([
    path("ws", Consumer.as_asgi()),
    re_path(r"", get_asgi_application()),
])
