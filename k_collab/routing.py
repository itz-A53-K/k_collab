from django.urls import path, re_path
from . import consumers  # Import your consumers

websocket_urlpatterns = [
    re_path(r"ws/(?P<user_id>\w+)/$", consumers.Consumer.as_asgi()),
]