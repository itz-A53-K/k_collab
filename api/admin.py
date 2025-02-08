from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone']

@admin.register(Message)
class messageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'timestamp']



class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 2

class taskAdmin(admin.ModelAdmin):
    inlines = [SubTaskInline]
    list_display = ['id', 'title', 'status', 'deadline']

admin.site.register(Task, taskAdmin)
admin.site.register(Team)
admin.site.register(Chat)


