"""
ASGI config for JournalApp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# import os
#
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "JournalApp.settings")
#
# application = get_asgi_application()
#
#


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import ClerkAuthMiddleware
from chat.routing import websocket_urlpatterns


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "JournalApp.settings")
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": ClerkAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
