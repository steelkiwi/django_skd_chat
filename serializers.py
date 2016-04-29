# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Thread, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ('id', 'content', 'sender')

    def get_sender(self, obj):
        return UserSerializer(instance=obj.sender).data


class ThreadSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ('id', 'participants',)

    def get_participants(self, obj):
        return [UserSerializer(instance=user).data for user in obj.participants.all()]

    def get_last_message(self, obj):
        return MessageSerializer(instance=obj.messages.last()).data
