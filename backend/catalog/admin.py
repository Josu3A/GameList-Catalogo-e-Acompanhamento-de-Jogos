from django.contrib import admin

from .models import Achievement, Developer, Game, Genre, Platform, Publisher


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ano_lancamento', 'status_publicacao', 'steam_appid')
    list_filter = ('status_publicacao', 'genres', 'platforms')
    search_fields = ('titulo',)
    filter_horizontal = ('genres', 'platforms', 'developers', 'publishers')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('nome',)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    search_fields = ('nome',)


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    search_fields = ('nome',)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ('nome',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('nome', 'game', 'steam_apiname')
    list_filter = ('game',)
    search_fields = ('nome', 'steam_apiname')
