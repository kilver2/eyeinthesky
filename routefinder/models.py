from django.db import models

class scrapedImage(models.Model):
    name = models.CharField(max_length=100)
    imageOnLocation = models.ImageField()