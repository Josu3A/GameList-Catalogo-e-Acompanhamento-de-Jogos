from django.contrib import admin

from .models import UserAchievement, UserGame


@admin.register(UserGame)
class UserGameAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'status', 'nota', 'platinado', 'fonte')
    list_filter = ('status', 'platinado', 'fonte')
    search_fields = ('user__nome', 'user__email', 'game__titulo')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'desbloqueada_em')
    search_fields = ('user__nome', 'achievement__nome')
