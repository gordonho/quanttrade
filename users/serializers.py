from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import APIKey

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'api_key', 'is_active_strategy', 'created_at']
        read_only_fields = ['id', 'created_at']


class APIKeySerializer(serializers.ModelSerializer):
    """API Key序列化器"""
    
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'broker', 'is_active', 'created_at']
        read_only_fields = ['id', 'key', 'created_at']
        extra_kwargs = {
            'secret': {'write_only': True}
        }

    def create(self, validated_data):
        import uuid
        validated_data['key'] = uuid.uuid4().hex
        return super().create(validated_data)
