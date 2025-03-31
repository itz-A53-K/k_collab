import json, requests
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from datetime import datetime
from api import models, serializers

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Add user to a general users group for new chat notifications
        await self.channel_layer.group_add(
            "users",
            self.channel_name
        )


    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):

        data = json.loads(text_data)
        message = data.get('msg')
        sender_id = data.get('user_id')
        receiver_id = data.get('receiver_id')


        if not (message and sender_id):
            print("Invalid data received from client")
            return
        
        if message == "initial":
            try:
                chats = await self.getUserChats(sender_id)

                for chat in chats: # create ws group for each chat
                    chatID = chat.id
                    await self.channel_layer.group_add(
                        f"chat_{chatID}",
                        self.channel_name
                    )

            except Exception as e:
                print("err: ",e)
                await self.close()
            return

        
        new_msgData, chat_data = await self.saveMsgToDB(data)

        if new_msgData and chat_data:
            
            group_name = f"chat_{chat_data['id']}"

            # Check if already in group
            if not any(group_name in group for group in self.groups):
                # Add to group if not already a member
                await self.channel_layer.group_add(
                    group_name,
                    self.channel_name
                )

            
            if receiver_id:
                # If this is a new chat (receiver_id present), send a special event
                await self.channel_layer.group_send(
                    "users",  # A group containing all online users
                    {
                        "type": "WS_newChat",
                        "msg_data": new_msgData,
                        'chat_data': chat_data,
                        'receiver_id': receiver_id
                    }
                )

            else:
                # Normal message in existing chat
                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "WS_chatMessage",
                        "msg_data": new_msgData,
                        'chat_data': chat_data
                    }
                )

    
    async def WS_chatMessage(self, event):
        # This is called when a message is received by the group.
        # It serializes the message and sends it to the WebSocket.

        await self.send(text_data=json.dumps({
            'msg_data': event['msg_data'],
            'chat_data': event['chat_data'],
        }))


    async def WS_newChat(self, event):

        receiver_id = event['receiver_id']

        # Only process if this consumer belongs to the receiver
        if str(receiver_id) == str(self.scope['user'].id):

            print("New chat event received")
            # Add receiver to the new chat's group
            await self.channel_layer.group_add(
                f"chat_{event['chat_data']['id']}",
                self.channel_name
            )
            
            # Send the new chat data to the client
            await self.send(text_data=json.dumps({
                'type': 'new_chat',
                'chat_data': event['chat_data'],
                'msg_data': event['msg_data']
            }))





    
    @database_sync_to_async
    def saveMsgToDB(self, data):
        print(data)

        try:
            msg = data.get('msg')
            chat_id = data.get('chat_id')
            sender_id = data.get('user_id')
            receiver_id = data.get('receiver_id')
            timestamp = datetime.now()
            
            class RequestMock:
                def __init__(self, user):
                    self.user = user
             

            sender = models.User.objects.get(id = sender_id)
            requests = RequestMock(sender)

            if chat_id:
                chat = models.Chat.objects.get(id = chat_id)

            else:          
                if not receiver_id:
                    raise ValueError("receiver_id is required for creating a new chat")
                
                receiver = models.User.objects.get(id = receiver_id)

                if sender == receiver:
                    raise ValueError("sender and receiver cannot be the same user")

                members = [sender, receiver]

                chat = models.Chat.objects.filter(members__in=members, is_group_chat = False).first()

                if not chat:
                    chat = models.Chat.objects.create(is_group_chat=False)
                    chat.members.set(members)
                    chat.save()


            if sender not in chat.members.all():
                raise PermissionError("User not a member of this chat")
            
            message = models.Message.objects.create(sender=sender, chat=chat, content=msg, timestamp = timestamp)
            print(message)

            msgSerializer = serializers.messageSerializer(message)
            chatSerializer = serializers.chatSerializer(chat, context={'request': requests})

            print("New message saved to DB")
            return [msgSerializer.data, chatSerializer.data]
        
        except (models.User.DoesNotExist, models.Chat.DoesNotExist) as e:
            print(f"Database lookup error: {str(e)}")
            return [None, None]
        except ValueError as e:
            print(f"Validation error: {str(e)}")
            return [None, None]
        except PermissionError as e:
            print(f"Permission error: {str(e)}")
            return [None, None]
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return [None, None]

    @database_sync_to_async
    def getUser(self, user_id):
        return User.objects.get(id=user_id)

    
    @database_sync_to_async
    def getUserChats(self, sender_id):
        user = User.objects.get(id=sender_id)
        return list(user.chats.all())
    
    
    @database_sync_to_async
    def getChatData(self, chat_id):
        try:
            chat = models.Chat.objects.get(id=chat_id)

            # Create a mock request object since serializer needs request context
            class RequestMock:
                def __init__(self, user):
                    self.user = user
                    
            request = RequestMock(chat.members.first())
            serializer = serializers.chatSerializer(chat, context={'request': request})
            return serializer.data

        except models.Chat.DoesNotExist:
            return None