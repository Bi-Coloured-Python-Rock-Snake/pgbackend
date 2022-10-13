"""
ASGI config for souslik project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/
"""

import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "souslik.settings")

application = get_asgi_application()

# wsgi_to_asgi
