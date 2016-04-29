#  require django >= 1.7
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DjangoChatConfig(AppConfig):
    name = 'django_ws_chat.chat'
    verbose_name = _('Django Chat')
