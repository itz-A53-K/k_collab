from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .manager import UserManager

import uuid

# Create your models here.

#email : abi@kcollab.in
#password : 1234

class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10, blank=True, null=True)
    dp =  models.ImageField(upload_to='user_dp', blank=True, null=True)

    designation = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email



class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True, null=True)
    icon = models.ImageField(upload_to='team_icons/', null=True, blank=True)
    members = models.ManyToManyField(User, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    chat = models.OneToOneField('Chat', on_delete=models.CASCADE, related_name='team', null=True, blank=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)

        if creating:
            # print("Creating a new chat for the team")
            chat = Chat.objects.create(is_group_chat=True)
            self.chat = chat
            self.save()

@receiver(m2m_changed, sender=Team.members.through)  # Listen to changes in the M2M table
def team_members_changed(sender, instance, action, **kwargs):
    instance.chat.members.set(instance.members.all())


    

class Task(models.Model):
    STATUS_CHOICES = [
        ('to do', 'To Do'),
        ('in progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    assigned_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    status = models.CharField(max_length=20, choices= STATUS_CHOICES, default="to do")
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.assigned_user and not self.assigned_team:
            raise ValueError("Either assigned_user or assigned_team must be set")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    members = models.ManyToManyField(User, related_name='chats', blank = True)
    is_group_chat = models.BooleanField(default=False, help_text= "True if it's a group chat, False for individual chat.")

    def __str__(self):
        return str(self.id) 
 
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.email}"


