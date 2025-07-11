import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# ⚠️ BU LINIYANI get_asgi_application() DAN KEYIN KO‘CHIRING!
django_asgi_app = get_asgi_application()

# Endi imports xavfsiz
import chat.routing  # ✅ Endi AppRegistry tayyor, xato bo‘lmaydi

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})