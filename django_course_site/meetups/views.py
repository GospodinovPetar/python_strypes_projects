"""
Views module for handling meetup listings, details, registrations,
and meetup requests.
"""

from django.core.mail import send_mail
from django.shortcuts import render, redirect

from meetups.forms import RegistrationForm, RequestMeetupForm
from meetups.models import Meetup, Participant


# Create your views here.


def meetups(request):
    """
    Display a list of all available meetups.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the 'meetups/index.html' template with context
                      containing the list of meetups.
    """
    meetups = Meetup.objects.all()
    return render(request, "meetups/index.html", {"meetups": meetups})


def meetup_details(request, meetup_slug):
    """
    Display details for a specific meetup and handle user registration.

    If the request method is GET, presents an empty registration form.
    If POST, validates form data, registers the participant, and redirects
    to the confirmation page.

    Args:
        request (HttpRequest): The HTTP request object.
        meetup_slug (str): The slug identifier of the meetup.

    Returns:
        HttpResponse: On GET or invalid POST, renders
                      'meetups/meetup-details.html' with form and meetup info.
                      On successful registration, redirects to
                      'confirm_registration' view.

    Raises:
        Meetup.DoesNotExist: If no meetup with the given slug is found,
                              renders the details template with
                              meetup_found=False.
    """
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

    except Meetup.DoesNotExist:
        # If the meetup doesn't exist, inform the user
        return render(
            request,
            "meetups/meetup-details.html",
            {"meetup_found": False},
        )


def confirm_registration(request, meetup_slug):
    """
    Render a confirmation page after successful registration.

    Args:
        request (HttpRequest): The HTTP request object.
        meetup_slug (str): The slug identifier of the meetup.

    Returns:
        HttpResponse: Renders 'meetups/registration_success.html' with
                      the organizer's email for further communication.

    Raises:
        Meetup.DoesNotExist: If the meetup slug is invalid.
    """
    meetup = Meetup.objects.get(slug=meetup_slug)
    return render(
        request,
        "meetups/registration_success.html",
        {
            "organizer_email": meetup.organizer_email,
        },
    )


def request_meetup(request):
    """
    Display a form for users to request a new meetup.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders 'meetups/request_meetup.html'.
    """
    return render(request, "meetups/request_meetup.html")
