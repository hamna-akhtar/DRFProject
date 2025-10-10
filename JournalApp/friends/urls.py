from django.urls import path, include
from . import views

app_name = 'friends'

urlpatterns = [
    path('', views.FriendRequestListCreateView.as_view(), name='friendrequest-list'),
    path('<int:pk>/', views.FriendRequestDetailView.as_view(), name='friendrequest-detail'),
    path('sent/', views.RequestsSentView.as_view(), name='friendrequest-sent'),
    path('received/', views.RequestsReceivedView.as_view(), name='friendrequest-received'),
]