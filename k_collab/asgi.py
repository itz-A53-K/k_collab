import django
django.setup()
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from k_collab.routing import websocket_urlpatterns  # Import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kcollab.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # Use it in URLRouter
        )
    ),
})