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
            'tasks': taskSerializer(tasks, many=True).data if tasks else {"msg": "No tasks found"},
            'last message': messageSerializer(lastMsg).data if lastMsg else {"msg": "No message"},  #latest message 
        }
        return Response(data, status=status.HTTP_200_OK)


class chatList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = chatSerializer

    def get_queryset(self):
        user = self.request.user
        chats = user.chats.annotate(
            last_message_time=Max('messages__timestamp')  # Get the max timestamp
        ).order_by('-last_message_time')

        return chats


class userList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = userSerializer



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

