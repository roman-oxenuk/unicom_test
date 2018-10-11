from django.urls import path

from lenders import views

urlpatterns = [
    path('', views.OffersView.as_view(), name='offers_list'),
    path('<int:pk>/', views.OffersDetailView.as_view(), name='offers_detail'),
]
