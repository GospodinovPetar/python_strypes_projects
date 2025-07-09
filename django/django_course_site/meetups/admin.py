from django.contrib import admin

from meetups.models import Meetup, Location, Participant


# Register your models here.
@admin.register(Meetup)
class MeetupAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "date", "location", "description")
    search_fields = ("name", "slug", "date", "location", "description")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "address")
    search_fields = ("name", "address")


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("email",)
    search_fields = ("email",)
