from django.core.mail import send_mail
from django.shortcuts import render, redirect

from meetups.forms import RegistrationForm, RequestMeetupForm
from meetups.models import Meetup, Participant


# Create your views here.


def meetups(request):
    meetups = Meetup.objects.all()
    return render(request, "meetups/index.html", {"meetups": meetups})


def meetup_details(request, meetup_slug):
    try:
        selected_meetup = Meetup.objects.get(slug=meetup_slug)
        if request.method == "GET":
            registration_form = RegistrationForm()
        else:
            registration_form = RegistrationForm(request.POST)
            if registration_form.is_valid():
                user_email = registration_form.cleaned_data["email"]
                participant, _was_created = Participant.objects.get_or_create(
                    email=user_email
                )
                selected_meetup.participant.add(participant)
                return redirect("confirm_registration", meetup_slug=meetup_slug)

        return render(
            request,
            "meetups/meetup-details.html",
            {
                "meetup_found": True,
                "meetup": selected_meetup,
                "form": registration_form,
            },
        )

    except Exception as exc:
        return render(request, "meetups/meetup-details.html", {"meetup_found": False})


def confirm_registration(request, meetup_slug):
    meetup = Meetup.objects.get(slug=meetup_slug)
    return render(
        request,
        "meetups/registration_success.html",
        {
            "organizer_email": meetup.organizer_email,
        },
    )

    return render(request, "meetups/request_meetup.html", {"form": form})
