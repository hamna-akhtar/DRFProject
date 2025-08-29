from .models import CustomUser
from .serializers import  UserSerializer
from rest_framework import generics
from .permissions import IsSelfOrReadOnly
from rest_framework import permissions



class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrReadOnly]

