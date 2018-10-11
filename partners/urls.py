from django.urls import path

from partners import views

urlpatterns = [
    path('', views.CustomerView.as_view(), name='customers_list'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customers_detail'),
]
