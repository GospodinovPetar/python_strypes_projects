from django import forms

from .models import Participant


class RegistrationForm(forms.Form):
    email = forms.EmailField(label="Email Address")


class RequestMeetupForm(forms.Form):
    name = forms.CharField(label="Your Name", max_length=100)
    email = forms.EmailField(label="Your Email")
    topic = forms.CharField(label="Topic Suggestion", widget=forms.Textarea)
