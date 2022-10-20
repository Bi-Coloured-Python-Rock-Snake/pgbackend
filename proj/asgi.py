
import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

from auth_middleware import AuthMiddlewareStack
from kitchen.ws import Consumer

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(Consumer.as_asgi()),
    "http": get_asgi_application(),
})
