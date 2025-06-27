from django.urls import path
from meetups import views

urlpatterns = [
    path('index/', views.index, name='index'),
]