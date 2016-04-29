# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
import threading
import time
import redis
import sockjs.tornado
from json import JSONEncoder
from uuid import UUID
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination

from .serializers import ThreadSerializer, MessageSerializer
from .models import Thread

JSONEncoder_olddefault = JSONEncoder.default


def JSONEncoder_newdefault(self, o):
    if isinstance(o, UUID): return str(o)
    return JSONEncoder_olddefault(self, o)


JSONEncoder.default = JSONEncoder_newdefault

User = get_user_model()


class NotificationConnection(sockjs.tornado.SockJSConnection):
    """Chat connection implementation"""
    # Class level variable
    participants = set()
    authorized = False
    user_pk = None
    closed = False

    def _get_channel(self):
        return 'user_chanel-{}'.format(self.user_pk)

    def on_open(self, info):
        # self.closed = False
        # Add client to the clients list
        self.participants.add(self)

    def _run_listener(self):
        pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        self.r = redis.Redis(connection_pool=pool)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)

        def cron(self):
            self.p.subscribe(self._get_channel())
            while not self.closed:
                raw_response = {
                    'method': 'GET'
                }
                message = self.p.get_message()
                if message:
                    raw_response['url'] = json.loads(message['data']).get('type_of_object', '')
                    raw_response['data'] = json.loads(message['data']).get('data', {})
                    raw_response['status_code'] = 200
                    self.broadcast(self.participants, json.dumps(raw_response))
                time.sleep(1)

        self.t = threading.Thread(target=cron, args=(self,))
        self.t.start()

    def _authorization(self, msg):
        """
        Method for authorization
        :param msg:
        :return:
        """
        raw_response = {
            'method': 'POST',
            'url': 'auth',
            'params': msg.get('params'),
        }

        if Token.objects.filter(user__pk=msg.get('params', {}).get('user_pk'),
                                key=msg.get('params', {}).get('token')).exists():
            if not self.authorized:
                self.authorized = True
                self.user_pk = msg.get('params', {}).get('user_pk')
                self.user = User.objects.get(pk=self.user_pk)
                self._run_listener()
            raw_response['status_code'] = 200
            raw_response['data'] = {}

        else:
            raw_response['errors'] = {
                '__all__': ['Token or user_pk is invalid']
            }
            raw_response['status_code'] = 400

        self.broadcast([self], json.dumps(raw_response))

    def _fetch_threads(self, msg):
        """
        Fetch history Threads

        :param msg:
        :return:
        """
        raw_response = {
            'method': 'GET',
            'url': 'threads',
            'params': msg.get('params'),
        }
        threads = self.user.threads.all()
        raw_response['data'] = [ThreadSerializer(instance=thread).data for thread in threads]
        raw_response['status_code'] = 200
        self.broadcast([self], json.dumps(raw_response))

    def _create_thread(self, msg):
        raw_response = {
            'method': 'POST',
            'url': 'threads',
            'params': msg.get('params'),
        }
        thread_serializer = ThreadSerializer(data=msg.get('params', {}))
        if thread_serializer.is_valid():
            user_request = thread_serializer.save()
            raw_response['data'] = ThreadSerializer(instance=user_request).data
            raw_response['status_code'] = 200
        else:
            raw_response['errors'] = thread_serializer.errors
            raw_response['status_code'] = 400

        self.broadcast(self.participants, json.dumps(raw_response))

    def _update_thread(self, msg):
        pass

    def _fetch_messages(self, msg):
        """
        Fetch history Messages

        :param msg:
        :return:
        """
        raw_response = {
            'method': 'GET',
            'url': 'messages',
            'params': msg.get('params'),
        }
        messages = []
        if msg.get('params', {}).get('thread'):
            thread = Thread.objects.get(pk=msg.get('params', {}).get('thread'))
            messages = thread.messages.all()

        raw_response['data'] = [MessageSerializer(instance=message).data for message in messages]
        raw_response['status_code'] = 200
        self.broadcast([self], json.dumps(raw_response))

    def _create_message(self, msg):
        raw_response = {
            'method': 'POST',
            'url': 'messages',
            'params': msg.get('params'),
        }
        message_serializer = MessageSerializer(data=msg.get('params', {}))
        if message_serializer.is_valid():
            message = message_serializer.save()
            raw_response['data'] = MessageSerializer(instance=message).data
            raw_response['status_code'] = 200
        else:
            raw_response['errors'] = message_serializer.errors
            raw_response['status_code'] = 400

        self.broadcast(self.participants, json.dumps(raw_response))

    def _update_message(self, msg):
        pass

    def on_message(self, message):

        msg = json.loads(message)

        # Authorize user
        if msg.get('method') == 'POST' and msg.get('url') == 'auth':
            self._authorization(msg=msg)

        if not self.authorized:
            self.close()
            return False

        # Fetch history Threads
        if msg.get('method') == 'GET' and msg.get('url') == 'threads':
            self._fetch_user_request_history(msg=msg)

        # Create Thread
        if msg.get('method') == 'POST' and msg.get('url') == 'threads':
            self._create_user_request(msg=msg)

        # Update Thread
        if msg.get('method') == 'PATCH' and msg.get('url') == 'threads':
            self._update_user_request(msg=msg)


        # Fetch Messages
        if msg.get('method') == 'GET' and msg.get('url') == 'messages':
            self._fetch_messages(msg=msg)

        if msg.get('method') == 'POST' and msg.get('url') == 'messages':
            self._create_message(msg=msg)

        if msg.get('method') == 'PATCH' and msg.get('url') == 'messages':
            self._update_message(msg=msg)

    def on_close(self):
        # Remove client from the clients list and broadcast leave message
        self.closed = True

        self.participants.remove(self)

        self.broadcast(self.participants, "Someone left.")
