import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application  # <-- To‘g‘ri joydan import qilyapmiz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import chat.routing  # django.setup() dan keyin

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # <-- To‘g‘ri
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
