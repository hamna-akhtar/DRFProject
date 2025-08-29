from django.urls import path
from . import views

app_name = 'journals'

urlpatterns = [
    path('', views.JournalEntryListCreateView.as_view(), name='journal-list-create'),
    path('<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal-detail'),
    path('my-journals/', views.MyJournalsView.as_view(), name='my-journals'),
    path('shared-with-me/', views.SharedWithMeView.as_view(), name='shared-with-me'),
    path('public/', views.PublicJournalsView.as_view(), name='public-journals'),

]