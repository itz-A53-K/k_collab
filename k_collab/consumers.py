import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from datetime import datetime
from api import models, serializers

User = get_user_model()


class Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            user_id = self.scope['url_route']['kwargs']['user_id']
            
            user = await self.getUser(user_id)
            if user is None:
                print("Invalid user ID")
                await self.close()
                return
            
            self.scope['user'] = user 

            await self.accept()

            # Add user to a general users group for new chat notifications
            await self.channel_layer.group_add(
                "users", self.channel_name
            )

        except Exception as e:
            print(f"Error in connect: {str(e)}")
            await self.close()


    async def disconnect(self, close_code):
        pass



    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', '')
            sender_id = data.get('user_id')

            if not sender_id:
                print("Invalid sender_id")
                return
            
            handlers = {
                'initial': self.handle_initial_connection,
                'message_create': self.handle_message_create,
                'task_create': self.handle_task_create,
            }

            handler = handlers.get(msg_type)
            if handler:
                await handler(data, sender_id)
            else:
                print(f"Unknown message type: {msg_type}")
        except Exception as e:
            print(f"Error in receive: {str(e)}")



    async def handle_initial_connection(self, data, sender_id):
        chats = await self.getUserChats(sender_id)
        for chat in chats: # create ws group for each chat
            chatID = chat.id
            await self.channel_layer.group_add(
                f"chat_{chatID}", self.channel_name
            )


    async def handle_message_create(self, data, sender_id):
        receiver_id = data.get('receiver_id')

        new_msgData, sender_chatData, receiver_chatData = await self.messageCreate_DB(data)

        if new_msgData and sender_chatData:
            chat_id = sender_chatData['id']
            group_name = f"chat_{chat_id}"

            # Check if already in group
            if not any(group_name in group for group in self.groups):
                # Add to group if not already a member
                await self.channel_layer.group_add(
                    group_name, self.channel_name
                )

            groupChat = sender_chatData['is_group_chat']

            if groupChat:
                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "WS_groupChatMsg",
                        "msg_data": new_msgData,
                        'chat_data': sender_chatData
                    }
                )
            else:                
                # Send immediate confirmation to sender
                await self.send(text_data=json.dumps({
                    'type': 'chat_notification',
                    'chat_data': sender_chatData,
                    'msg_data': new_msgData
                }))

                await self.channel_layer.group_send(
                    "users",  # A group containing all online users
                    {
                        "type": "WS_individualChatMsg",
                        "msg_data": new_msgData,
                        'chat_data': receiver_chatData,
                        'receiver_id': receiver_id,
                        'alt_receiver_id': None if receiver_id else sender_chatData['metaData']['id']
                    }
                )


    async def handle_task_create(self, data, sender_id):
        task_data= await self.taskCreate_DB(data)

        if not task_data:
            return
        
        # Send notification to all relevant users
        await self.channel_layer.group_send(
            "users",
            {
                "type": "WS_taskNotification",
                "task_data": task_data,
                'creator_id': sender_id,
            }
        )






    
    async def WS_groupChatMsg(self, event):
        # This is called when a message is received by the group.
        # It serializes the message and sends it to the WebSocket.

        await self.send(text_data=json.dumps({
            'type': 'chat_notification',
            'msg_data': event['msg_data'],
            'chat_data': event['chat_data'],
        }))


    async def WS_individualChatMsg(self, event):
        user_id = str(self.scope['user'].id)
        receiver_id = event.get('receiver_id')
        alt_receiver_id = event.get('alt_receiver_id')
        group_name = f"chat_{event['chat_data']['id']}"
        chat_data = event['chat_data']

        if receiver_id:
            # Add receiver to the new chat's group
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
        
        if user_id in [str(receiver_id), str(alt_receiver_id)]:
            # Send the new chat data to the client
            await self.send(text_data=json.dumps({
                'type': 'chat_notification',
                'chat_data': chat_data,
                'msg_data': event['msg_data']
            }))


    async def WS_taskNotification(self, event):
        current_user_id = str(self.scope['user'].id)

        task_data = event['task_data']
        creator_id = event.get('creator_id')

        if creator_id and current_user_id == str(creator_id):
            await self.send(text_data=json.dumps({
                'type': 'task_create_confirmation',
                'task_data': task_data,
                'created': True
            }))
            
        user_id = task_data.get('assigned_user_id')
        team_id = task_data.get('assigned_team_id')

        if user_id and current_user_id == str(user_id):
            await self.send(text_data=json.dumps({
                'type': 'user_task_notification',
                'task_data': task_data,
            }))
            return
        
        if team_id:
            teamMembers = await self.getTeamMembers(team_id)

            print(current_user_id)
            if current_user_id in teamMembers:                
                print("yes ", current_user_id)
                await self.send(text_data=json.dumps({
                    'type': 'team_task_notification',
                    'task_data': task_data,
                }))





    
    @database_sync_to_async
    def messageCreate_DB(self, data):
        """Saves a new message to the database and returns the message data and chat data.
        Args:
            data (dict): The data containing message details.

        Returns:
            tuple: (msgData, sender_chatData, receiver_chatData) - A tuple containing the new message data and chat data.
        """
        try:
            msg = data.get('msg')
            chat_id = data.get('chat_id')
            sender_id = data.get('user_id')
            receiver_id = data.get('receiver_id')
            timestamp = datetime.now()

            sender = models.User.objects.get(id = sender_id)

            if chat_id:
                # Existing chat
                chat = models.Chat.objects.get(id = chat_id)
            else:          
                if not receiver_id:
                    raise ValueError("receiver_id is required for creating a new chat")
                
                receiver = models.User.objects.get(id = receiver_id)

                if sender == receiver:
                    raise ValueError("sender and receiver cannot be the same user")

                chat = models.Chat.objects.filter(
                    members=sender,
                    is_group_chat=False
                ).filter(
                    members=receiver
                ).first()

                if not chat:
                    chat = models.Chat.objects.create(is_group_chat=False)
                    chat.members.set([sender, receiver])
                    chat.save()
                    # print("New chat created")

            if sender not in chat.members.all():
                raise PermissionError("User not a member of this chat")
            
            message = models.Message.objects.create(sender=sender, chat=chat, content=msg, timestamp = timestamp)

            
            sender_chatData = serializers.chatSerializer(chat, context={'user_id': sender_id}).data

            if chat.is_group_chat:
                receiver_chatData = None
            else:
                receiver_id = chat.members.exclude(id=sender_id).first().id
                receiver_chatData = serializers.chatSerializer(chat, context={'user_id': receiver_id}).data

            msg_data = serializers.messageSerializer(message).data

            return [msg_data, sender_chatData, receiver_chatData]
        
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
    def taskCreate_DB(self, data):
        """Saves a new task to the database and returns the task data.
        Args:
            data (dict): The data containing task details.
        Returns:
            dict: 
        """
        try:
            task_data = data.get('task_data')

            title = task_data.get('title')
            description = task_data.get('desc')
            deadline = task_data.get('deadline')
            assigned_user = task_data.get('assigned_user')
            assigned_team = task_data.get('assigned_team')

            user = None
            team = None

            if assigned_user:
                user_id = assigned_user.split('(')[-1].strip(')')
                user = models.User.objects.get(id=user_id)
            elif assigned_team:
                team_id = assigned_team.split('(')[-1].strip(')')
                team = models.Team.objects.get(id=team_id)
            
            task = models.Task.objects.create(
                title=title,
                description=description,
                deadline=deadline,
                assigned_user = user,
                assigned_team = team,
            )

            new_taskData = serializers.task_subTaskSerializer(task).data
            #add user, team to new_taskData
            if user:
                new_taskData['assigned_user_id'] = user_id
            if team:
                new_taskData['assigned_team_id'] = team_id


            return new_taskData
        
        except Exception as e:
            print(f"error: {str(e)}")
            return None


    @database_sync_to_async
    def getUser(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except Exception as e:
            print(f"Error fetching user: {str(e)}")
            return None
    

    @database_sync_to_async
    def getUserChats(self, sender_id):
        user = User.objects.get(id=sender_id)
        return list(user.chats.all())
    
    
    @database_sync_to_async
    def getTeamMembers(self, team_id):
        try:
            team = models.Team.objects.prefetch_related('members').get(id=team_id)
            return {str(member.id) for member in team.members.all()}
        except models.Team.DoesNotExist:
            return set()