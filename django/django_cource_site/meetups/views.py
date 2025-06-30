from django.shortcuts import render
# Create your views here.

def meetups(request):
    meetups = [
        {'title': 'A first meetup', 'location': 'Amsterdam', 'slug': 'first-meetup'},
        {'title': 'A second meetup', 'location': 'New York', 'slug': 'second-meetup'},
    ]
    return render(request, 'meetups/index.html', {
        'meetups': meetups,
        'show_meetups': True
    })

def meetup_details(request, meetup_slug):
    selected_meetup = {
        'title': 'The first meetup',
        'description': 'This is the first meetup'
    }
    return render(request, 'meetups/meetup-details.html', {
        'meetup_title': selected_meetup['title'],
        'meetup_description': selected_meetup['description']
    }
)