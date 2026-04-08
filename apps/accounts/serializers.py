from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, Notification


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'role', 'password', 'confirm_password')

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(
            email=validated_data['email'],
            role=validated_data['role'],
            password=validated_data['password'],
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'role', 'is_staff', 'date_joined')
        read_only_fields = ('id', 'is_staff', 'date_joined')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'message', 'link', 'is_read', 'created_at')
        read_only_fields = ('id', 'type', 'title', 'message', 'link', 'created_at')
