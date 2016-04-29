# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import sockjs.tornado
import tornado
import tornado.ioloop
import tornado.web
from django.conf import settings
from django.core.management.base import BaseCommand

from django_ws_chat.chat.sockets import NotificationConnection


class Command(BaseCommand):
    def handle(self, *args, **options):
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

        # 1. Create notification router

        NotificationRouter = sockjs.tornado.SockJSRouter(NotificationConnection, '/notification')


        # 2. Create Tornado application
        app = tornado.web.Application(NotificationRouter.urls,
                                      autoreload=settings.DEBUG
                                      )

        # 3. Make Tornado app listen on port WebSocketPort
        app.listen(settings.WEB_SOCKET_PORT)

        # 4. Start IOLoop
        try:
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
