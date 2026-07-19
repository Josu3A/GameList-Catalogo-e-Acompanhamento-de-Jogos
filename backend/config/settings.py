"""
Configurações do projeto GameList (backend Django + DRF).

Valores sensíveis/ambiente vêm do arquivo .env (ver .env.example).
Banco: PostgreSQL 18 local, porta 5433 (ver LOG.md do repositório).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-chave-de-desenvolvimento-trocar-em-producao',
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # terceiros
    'rest_framework',
    'django_filters',
    'corsheaders',
    # apps do projeto
    'accounts',
    'catalog',
    'library',
    'social',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Banco de dados — PostgreSQL (porta 5433 = instância PG 18 local; ver LOG.md)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'gamelist'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5433'),
    }
}


# Usuário customizado (tabela `users` do esquema do projeto)

AUTH_USER_MODEL = 'accounts.User'


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# CORS/CSRF — origens de desenvolvimento do futuro frontend (React)

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:5173',
).split(',')
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS


# Integração com a Steam (ver CONTEXTO_PROJETO §6)
# - STEAM_API_KEY: Steam Web API Key (GetOwnedGames/GetSchemaForGame/
#   GetPlayerAchievements/GetPlayerSummaries). Fica só aqui, nunca no frontend.
#   O login OpenID e o autofill da loja (Storefront) NÃO dependem dela.
# - FRONTEND_URL: destino dos redirects pós-login OpenID (SPA React).

STEAM_API_KEY = os.environ.get('STEAM_API_KEY', '')

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

# Integração com a RAWG (carrossel de "Próximos Lançamentos" da Home,
# ver catalog/rawg.py). Chave simples via query param (sem OAuth), registrar
# em rawg.io/apidocs. Fica só aqui, nunca no frontend. Sem ela, o endpoint
# degrada para lista vazia.
RAWG_API_KEY = os.environ.get('RAWG_API_KEY', '')


# Internationalization

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

# Media (uploads dos usuários — ex.: avatares de perfil).
# A coluna avatar_url guarda só o caminho relativo (ex.: avatars/<uuid>.jpg);
# em DEBUG o próprio Django serve os arquivos a partir de MEDIA_ROOT (ver config/urls.py).
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Teto de upload em memória (2,5 MB) — o avatar é validado em 2 MB no serializer.
DATA_UPLOAD_MAX_MEMORY_SIZE = int(2.5 * 1024 * 1024)
FILE_UPLOAD_MAX_MEMORY_SIZE = int(2.5 * 1024 * 1024)

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
