from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListView.as_view(), name='user-list'),
    path('discover/', views.DiscoverFriendsView.as_view(), name='user-discover'),
    path('my-profile/', views.MyProfileView.as_view(), name='my-profile'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
]
