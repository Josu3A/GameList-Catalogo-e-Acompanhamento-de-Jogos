from django.contrib import admin

from .models import Friendship, List, Notification

# ReviewLike e ListItem têm PK composta (CompositePrimaryKey) e, por limitação do
# Django Admin, não podem ser registrados nem usados como inline — são geridos
# pela API (social/views.py) e pelos modelos-pai.


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user', 'friend', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__nome', 'user__email', 'friend__nome', 'friend__email')
    readonly_fields = ('created_at',)


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'publica', 'created_at')
    list_filter = ('publica',)
    search_fields = ('nome', 'user__nome', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'actor', 'lida', 'created_at')
    list_filter = ('tipo', 'lida')
    search_fields = ('user__nome', 'user__email')
    readonly_fields = ('created_at',)
