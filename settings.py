from django.conf import settings


DJANGO_CHAT_REDIS_PORT = getattr(settings, 'DJANGO_CHAT_REDIS_PORT', 6379)

DJANGO_CHAT_REDIS_HOST = getattr(settings, 'DJANGO_CHAT_REDIS_HOST', 'localhost')

DJANGO_CHAT_WEB_SOCKET_PORT = getattr(settings, 'DJANGO_CHAT_WEB_SOCKET_PORT', 9500)
