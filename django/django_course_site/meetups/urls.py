from django.urls import path
from meetups import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.meetups, name='meetups'),
    path('meetups/<slug:meetup_slug>/', views.meetup_details, name='meetup-details'),
    #our-domain.com/meetups/<dynamic-path>
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)