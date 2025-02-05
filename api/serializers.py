from rest_framework import serializers
from .models import *


class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'designation', 'dp', 'ip_addr', 'port']


class chatSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    class Meta:
        model = Chat
        fields = ['id', 'members', 'is_group_chat'] 
    
    def get_members(self,obj):
        users = userSerializer(obj.members, many = True).data
        filtered_users = [
            {
                "name": user["name"],
                "email": user["email"],
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
            'name': obj.sender.name,
            'email': obj.sender.email,
        }
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['timestamp'] = instance.timestamp.strftime("%d %b %Y %I:%M:%S %p")
        return data

    
