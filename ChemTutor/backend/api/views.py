from rest_framework import viewsets
from .models import ExampleTask
from .serializers import ExampleTaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = ExampleTask.objects.all()
    serializer_class = ExampleTaskSerializer
