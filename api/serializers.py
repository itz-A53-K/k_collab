from rest_framework import serializers
from .models import *
from datetime import datetime


class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email','dp']
        # fields = ['id', 'name', 'email', 'phone', 'designation', 'dp', 'ip_addr', 'port']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.dp:
            data['dp'] = str(instance.dp.url)
        else:
            data['dp'] = None
        return data


class chatSerializer(serializers.ModelSerializer):
    metaData = serializers.SerializerMethodField()
    last_msg = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'metaData', 'last_msg', 'is_group_chat'] 
        
    
    def get_metaData(self, obj):
        user_id = self.context.get('user_id') or self.context['request'].user.id
        if obj.is_group_chat:
            id = None
            name = f"{obj.team.name} (Group)"
            icon = str(obj.team.icon.url) if obj.team.icon else None
        else:
            otherMember  = obj.members.exclude(id=user_id).first()
            id = otherMember.id
            name = otherMember.name
            icon = str(otherMember.dp.url) if otherMember.dp else None

        return {"id": id, "name": str(name), "icon": icon}
        
    def get_last_msg(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return messageSerializer(last_msg).data
        return {"msg": "No message yet"}

    

class teamSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'icon', 'members']
    
    def get_members(self, obj):
        members = obj.members.all()
        return userSerializer(members, many=True).data
    
    def to_representation(self, instance):
        data = super().to_representation(instance)        
        data['icon'] = str(instance.icon.url) if instance.icon else None
        return data



class task_subTask_detailSerializer(serializers.ModelSerializer):
    is_subtask = serializers.SerializerMethodField()
    parent_task_id = serializers.SerializerMethodField()
    subtaskCount = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Task  # Start with Task, we will override as needed.
        fields = ['id', 'title', 'description', 'deadline', 'status', 'is_subtask', 'parent_task_id', 'subtaskCount', 'progress']

    def get_is_subtask(self, obj):
        return isinstance(obj, SubTask)

    def get_parent_task_id(self, obj):
        if isinstance(obj, SubTask):
            return obj.task.id
        return None

    def get_subtaskCount(self, obj):
        if isinstance(obj, Task):
            return obj.subtasks.count()
        return 0
    
    def get_progress(self, obj):
        if isinstance(obj, Task):
            total_subtasks = obj.subtasks.count()
            completed_subtasks = obj.subtasks.filter(status='completed').count()
            if total_subtasks == 0:
                if obj.status == 'completed':
                    return 100
                return 0
            return int((completed_subtasks / total_subtasks) * 100)
        return None
    def to_representation(self, instance):
        if isinstance(instance, SubTask):
            self.Meta.model = SubTask
        else:
            self.Meta.model = Task
        return super().to_representation(instance)

class task_subTaskSerializer(serializers.ModelSerializer):
    is_subtask = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fields = ['id', 'title','deadline', 'status', 'is_subtask']

    def get_is_subtask(self, obj):
        return isinstance(obj, SubTask)


    def to_representation(self, instance):
        if isinstance(instance, SubTask):
            self.Meta.model = SubTask
        else:
            self.Meta.model = Task
        return super().to_representation(instance)


class messageSerializer(serializers.ModelSerializer):
    sender  = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'timestamp']

    def get_sender(self, obj):
        return {
            'id': obj.sender.id,
            'name': obj.sender.name,
            'email': obj.sender.email,
            'dp': str(obj.sender.dp.url) if obj.sender.dp else None
        }
    
    def to_representation(self, instance):

        data = super().to_representation(instance)
        timestamp = instance.timestamp

        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        data['timestamp'] = timestamp.strftime("%d-%m-%y %I:%M %p")
        return data

    
class broadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broadcast
        fields = ['id', 'title', 'message', 'created_at']
