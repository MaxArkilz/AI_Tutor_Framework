from rest_framework import serializers
from .models import ExampleTask


class ExampleTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleTask
        fields = '__all__'
