from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone']
admin.site.register(Team)
admin.site.register(Task)
admin.site.register(Chat)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'timestamp']



