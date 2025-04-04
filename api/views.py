from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Max
from datetime import datetime, timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token


from .models import *
from .serializers import *
from itertools import chain
import json


class taskCreate(generics.CreateAPIView):
    serializer_class = task_subTaskSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        print(data)

        return Response(data, status=status.HTTP_200_OK)



class task_subTaskViewUpdate(generics.RetrieveUpdateAPIView):
    serializer_class= task_subTask_detailSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg  = 'task_id'
    

    def get_object(self):
        pk = self.kwargs.get('task_id')        
        is_subtask = self.request.query_params.get('isSubtask') or self.request.data.get('isSubtask')

        try:
            if is_subtask.lower() == "true":
                return SubTask.objects.get(pk=pk)
            else:
                return Task.objects.get(pk=pk)
        except (SubTask.DoesNotExist, Task.DoesNotExist): 
            return None
        except Exception as e:
            print(e)
            return None
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({"detail": "Task or Subtask not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        newStatus = request.data.get('newStatus')
        if instance is None:
            return Response({"detail": "Task or Subtask not found."}, status=status.HTTP_404_NOT_FOUND)

        if newStatus:
            instance.status = newStatus
            instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
        

class task_subTaskList(generics.ListAPIView):
    serializer_class = task_subTaskSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        filter = self.request.query_params.get('filter', "to do") or self.request.data.get('filter', "to do")

        tasks = list(user.tasks.filter(status = filter))
        subtasks = list(user.subtasks.filter(status = filter))
        combined_list = list(chain(tasks, subtasks))

        combined_list.sort(key=lambda item: item.deadline)

        return combined_list 



class teamListCreate(generics.ListCreateAPIView):
    serializer_class = teamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        teams = user.teams.all().order_by('-created_at')
        return teams



#tasks and other content related to a specific team
class teamContent(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        user = request.user
        tasks = team.tasks.all()
        lastMsg = team.chat.messages.order_by('-timestamp').first()

        data = {
            'team': teamSerializer(team).data,
            'tasks': task_subTaskSerializer(tasks, many=True).data if tasks else {"msg": "No task yet"},
            'last message': messageSerializer(lastMsg).data if lastMsg else {"msg": "No message"},  #latest message 
        }
        return Response(data, status=status.HTTP_200_OK)



class chatDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = chatSerializer

    def get_object(self):
        chat_id = self.kwargs.get('chat_id')
        return get_object_or_404(Chat, id=chat_id)

    def retrieve(self, request, *args, **kwargs):
        chat = self.get_object()
        chatSerializer = self.get_serializer(chat)

        messages = chat.messages.all().order_by('timestamp')
        msgSerializer = messageSerializer(messages, many=True)

        return Response(
            {
                'chat': chatSerializer.data,
                'messages': msgSerializer.data
            },
            status = status.HTTP_200_OK
        )



class chatList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = chatSerializer

    def get_queryset(self):
        user = self.request.user
        filter = self.request.query_params.get('filter', 'all').lower()
        
        if filter == 'groups':
            chats = user.chats.filter(is_group_chat = True).annotate(
                last_message_time=Max('messages__timestamp')  # Get the max timestamp
            ).order_by('-last_message_time')
        else:
            chats = user.chats.annotate(
                last_message_time=Max('messages__timestamp')
            ).order_by('-last_message_time')
        
        return chats
    

class userList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = userSerializer

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.exclude(id=user.id)
        return qs



class userDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        details = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'isAdmin': user.isAdmin,
            'dp': user.dp.url if user.dp else None
        }

        return Response(details, status=status.HTTP_200_OK)



class logoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.user.auth_token
        if token:
            try:
                Token.objects.get(key = token).delete()
            except Token.DoesNotExist:
                print("Invalid Token")
                
        response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        response.delete_cookie('authToken')
        return response



class loginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if email is None or password is None:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Login successful',
                'authToken': token.key,
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


