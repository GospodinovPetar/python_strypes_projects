from django.shortcuts import render

from meetups.models import Meetup


# Create your views here.

def meetups(request):
    meetups = Meetup.objects.all()
    return render(request, 'meetups/index.html', {
        'meetups': meetups
    })

def meetup_details(request, meetup_slug):
    try:
        selected_meetup = Meetup.objects.get(slug=meetup_slug)
        return render(request, 'meetups/meetup-details.html', {
            # 'meetup_title': selected_meetup.name,
            # 'meetup_description': selected_meetup.description,
            # 'meetup_location': selected_meetup.location,
            # 'meetup_image': selected_meetup.image,
            'meetup_found': True,
            'meetup': selected_meetup,
        }
  )
    except Exception as exc:
        return render(request, 'meetups/meetup-details.html', {
            'meetup_found' : False
        })
