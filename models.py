# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext as _
from django_extensions.db.models import TimeStampedModel
import json
import redis
from .settings import DJANGO_CHAT_REDIS_HOST, DJANGO_CHAT_REDIS_PORT

User = get_user_model()


class Thread(TimeStampedModel):
    participants = models.ManyToManyField(User, verbose_name=_('participants'), related_name='threads')

    def get_channel(self, user=None):
        if user is None:
            user = self.thread.creator
        return 'user_chanel-{}'.format(user.pk)

    def send_to_redis(self, user=None):

        from django_ws_chat.chat.serializers import ThreadSerializer
        if user is None:
            user = self.thread.creator
        pool = redis.ConnectionPool(host=DJANGO_CHAT_REDIS_HOST, port=DJANGO_CHAT_REDIS_PORT, db=0)
        r = redis.Redis(connection_pool=pool)
        message = {
            'type_of_object': 'threads',
            'data': ThreadSerializer(instance=self).data
        }
        r.publish(self.get_channel(user), json.dumps(message))


class Message(TimeStampedModel):
    sender = models.ForeignKey(User, verbose_name=_('Sender'), related_name='messages')
    thread = models.ForeignKey(Thread, verbose_name=_('Thread'), related_name='messages')
    read_by = models.ManyToManyField(User, verbose_name=_('Read by'))
    content = models.TextField(verbose_name=_('Content'))

    def get_channel(self, user=None):
        if user is None:
            user = self.thread.creator
        return 'user_chanel-{}'.format(user.pk)

    def send_to_redis(self, user=None):

        from django_ws_chat.chat.serializers import MessageSerializer
        if user is None:
            user = self.thread.creator
        pool = redis.ConnectionPool(host=DJANGO_CHAT_REDIS_HOST, port=DJANGO_CHAT_REDIS_PORT, db=0)
        r = redis.Redis(connection_pool=pool)
        message = {
            'type_of_object': 'messages',
            'data': MessageSerializer(instance=self).data
        }
        r.publish(self.get_channel(user), json.dumps(message))
