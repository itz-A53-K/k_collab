from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginView.as_view(), name='login'),
    path('logout/', views.logoutView.as_view(), name='logout'),

    path('users/', views.userList.as_view(), name='user_list'),
    path('user/details/', views.userDetail.as_view(), name='user_details'),

    path('chats/', views.chatList.as_view(), name='chat_list'),
    path('chats/<uuid:chat_id>/', views.chatDetail.as_view(), name='chat_content'),

    path('teams/', views.teamListCreate.as_view(), name='team_list_create'),
    path('teams/<uuid:team_id>/', views.teamContent.as_view(), name='team_content'),

    path('tasks/', views.task_subTaskList.as_view(), name='task_list'),
    path('tasks/<int:task_id>/', views.task_subTaskViewUpdate.as_view(), name='task_view_update'),
]
