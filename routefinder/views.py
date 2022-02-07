from django.shortcuts import render, redirect, reverse
from django.conf import settings
from .models import scrapedImage
from CCTV.mixins import Directions, Images, Detect, pin, audio
import urllib
import requests
import google_streetview.api
import os, os.path


'''
Basic view for home, introduction
'''
def index(request):
	return render(request, 'routefinder/home.html')

def introduction(request):
	return render(request, 'routefinder/introduction.html')

def eye(request):
	return render(request, 'routefinder/eye.html')

def info(request):
	return render(request, 'routefinder/info.html')

def further_research(request):
	return render(request, 'routefinder/further_research.html')

def end(request):
	return render(request, 'routefinder/end.html')
	
	
'''
Basic view for routing 
'''

def route(request):

	context = {
	"google_api_key": settings.GOOGLE_API_KEY,
	"base_country": settings.BASE_COUNTRY}
	return render(request, 'routefinder/route.html', context)


'''
Basic view for displaying a map 
'''
def map(request):

	dir = 'routefinder/scraped'
	detecteddir = 'routefinder/detected'
	for f in os.listdir(dir):
		os.remove(os.path.join(dir, f))

	lat_a = request.GET.get("lat_a", None)
	long_a = request.GET.get("long_a", None)
	lat_b = request.GET.get("lat_b", None)
	long_b = request.GET.get("long_b", None)

	#only call API if all 4 addresses are added
	if lat_a and lat_b:
		directions = Directions(
			lat_a= lat_a,
			long_a=long_a,
			lat_b = lat_b,
			long_b=long_b,
			)
		steplocations = Images(
			lat_a= lat_a,
			long_a=long_a,
			lat_b = lat_b,
			long_b=long_b,
			)
	else:
		return redirect(reverse('route'))

	
	params = {
    'size': '600x600',
    'location': steplocations,
    'heading': '151.78',
    'pitch': '-0.76',
    'key': settings.GOOGLE_API_KEY
	}

	api_list = google_streetview.helpers.api_list(params)
	results = google_streetview.api.results(api_list)
	results.download_links(dir)
	Detect()

	camerasfound = len(os.listdir(detecteddir))
	pins = pin()
	audio()

	context = {
	"google_api_key": settings.GOOGLE_API_KEY,
	"base_country": settings.BASE_COUNTRY,
	"lat_a": lat_a,
	"long_a": long_a,
	"lat_b": lat_b,
	"long_b": long_b,
	"origin": f'{lat_a}, {long_a}',
	"destination": f'{lat_b}, {long_b}',
	"directions": directions,
	"camerasfound": camerasfound,
	"pins" : pins,
	}

	return render(request, 'routefinder/map.html', context)

