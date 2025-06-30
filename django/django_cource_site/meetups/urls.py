from django.urls import path
from meetups import views

urlpatterns = [
    path('meetups/', views.meetups, name='meetups'),
    path('meetups/<slug:meetup_slug>/', views.meetup_details, name='meetup-details'), #our-domain.com/meetups/<dynamic-path>
]