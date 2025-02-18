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


class messageListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get('chat_id') or request.data.get('chat_id')
        if not chat_id:
            return Response({"error": "chat_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        chat = get_object_or_404(Chat, id=chat_id)
        messages = chat.messages.all().order_by('timestamp') 
        msgserializer = messageSerializer(messages, many=True)
        return Response({"chat": chatSerializer(chat).data, "messages": msgserializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        sender = self.request.user
        # sender = get_object_or_404(User, id = 2)
        chat_id = request.data.get('chat_id')
        receiver_id = request.data.get('receiver_id')
        content = request.data.get('content')

        if not content:
            return Response({"error": "Content cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        if chat_id:
            chat = get_object_or_404(Chat, id=chat_id)            
        else:
            if not receiver_id:
                return Response({"error": "receiver_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            receiver = User.objects.filter(id=receiver_id).first()
            if not receiver:
                return Response({"error": "Invalid receiver_id."}, status=status.HTTP_404_NOT_FOUND)
            
            if sender == receiver:
                return Response({"error": "Sender and receiver cannot be the same"}, status=status.HTTP_400_BAD_REQUEST)
            
            members = [sender, receiver] 
            chat = Chat.objects.filter(members__in=members, is_group_chat = False).first()
            if not chat:
                chat = Chat.objects.create(is_group_chat=False)
                chat.members.set(members)
                chat.save()

        if sender not in chat.members.all():
            return Response({"error": "You are not a member of this chat"}, status=status.HTTP_403_FORBIDDEN)
        
        message = Message.objects.create(sender=sender, content=content, chat=chat)
        serializer = messageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
                


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
            'tasks': taskSerializer(tasks, many=True).data if tasks else {"msg": "No tasks yet"},
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
    

# class chatList(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self):
#         return Response({"msg":"error"}, status= status.HTTP_404_NOT_FOUND)

class userList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = userSerializer



class updateUserIP(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # ip_addr = request.META['REMOTE_ADDR']
        ip_addr = '127.0.0.2'
        port = request.data.get('port', 8000)

        if not ip_addr or not port:
            return Response({"error": "Both IP and Port is required"}, status= status.HTTP_400_BAD_REQUEST)

        user.ip_addr = ip_addr
        user.port = port
        user.save()

        return Response({"message": "IP updated", "uID": user.id, "uName": user.name, 'ip': ip_addr, "port": port}, status= status.HTTP_200_OK )



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
                'user':{
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                }
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


