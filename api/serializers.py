from rest_framework import serializers
from .models import *


class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'designation', 'dp', 'ip_addr', 'port']


class chatSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    metaData = serializers.SerializerMethodField()
    class Meta:
        model = Chat
        fields = ['id', 'metaData', 'members', 'is_group_chat'] 
        
    
    def get_metaData(self, obj):
        user = self.context['request'].user
        if obj.is_group_chat:
            name = f"{obj.team.name} (Group)"
            icon = obj.team.icon
        else:
            otherMember  = obj.members.exclude(id=user.id).first()
            name = otherMember.name
            icon = otherMember.dp

        return {"name": str(name).capitalize(), "icon": str(icon)}
        
   
    def get_members(self, obj):
        user = self.context['request'].user.id
        users = userSerializer(obj.members.exclude(id = user ), many = True).data
        filtered_users = [
            {
                "name": user["name"],
                "ip_addr": user["ip_addr"],
                "port": user["port"]
            }
            for user in users
        ]

        return filtered_users
    

class teamSerializer(serializers.ModelSerializer):
    members = serializers.StringRelatedField(many=True)
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'icon', 'members']


class taskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'deadline']


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
        }
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['timestamp'] = instance.timestamp.strftime("%d-%m-%y %I:%M %p")
        return data

    
