# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import sys
from django.core.management import BaseCommand
from expertmatch.users.factories import UserFactory, RequestNotificationFactory


class Command(BaseCommand):
    def handle(self, *args, **options):
        sys.stdout.write('Started fill db\r\n')

        sys.stdout.write('Starting create Users\r\n')
        UserFactory.create_batch(50)
        sys.stdout.write('Created 50 Users\r\n')

        sys.stdout.write('Start creating 50 RequestNotifications\r\n')
        RequestNotificationFactory.create_batch(50)
        sys.stdout.write('Created 50 RequestNotification\r\n')

        sys.stdout.write('Completed fill db\r\n')
