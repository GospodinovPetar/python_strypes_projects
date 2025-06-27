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