import asyncio
import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

from auth_middleware import AuthMiddlewareStack
from kitchen.ws import Consumer
from proj.pwt import wrap_co

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(Consumer.as_asgi()),
    "http": get_asgi_application(),
})


async def application(scope, receive, send, application=application):
    obj = Obj(application=application, scope=scope, receive=receive, send=send)
    return await obj

class Obj:
    def __init__(self, *, application, scope, receive, send):
        self.scope = scope
        self.receive = receive
        self.send = send
        self.application = application

    @wrap_co
    async def _await__(self):
        return await self.application(self.scope, self.receive, self.send)

    def __await__(self):
        task = self._await__()
        task = asyncio.create_task(task)
        yield from task