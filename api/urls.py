from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginView.as_view(), name='login'),
    path('chats/', views.chatList.as_view(), name='chat_list'),
    path('teams/', views.teamListCreate.as_view(), name='team_list_create'),
    path('teams/<uuid:team_id>/', views.teamContent.as_view(), name='team_content'),
]
