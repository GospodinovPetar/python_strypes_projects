from django.contrib import admin

from meetups.models import Meetup


# Register your models here.
@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'slug', 'description')