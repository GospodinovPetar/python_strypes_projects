from django.db import models

# Create your models here.
class Meetup(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='images/', null=True, blank=True)
