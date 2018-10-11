from django.urls import path

from applications import views

urlpatterns = [
    path('', views.ApplicationsView.as_view(), name='applications_list'),
    path('<int:pk>/', views.ApplicationsDetailView.as_view(), name='applications_detail')
]
