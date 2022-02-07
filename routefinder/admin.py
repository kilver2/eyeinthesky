from django.contrib import admin

from .models import scrapedImage

# Register your models here.
class scrapedImageAdmin(admin.ModelAdmin):
      list_display = ['name', 'imageOnLocation']

admin.site.register(scrapedImage, scrapedImageAdmin)