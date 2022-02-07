from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import urlencode
import urllib
import requests
import google_streetview.api
import requests
import json
import datetime
from humanfriendly import format_timespan
from django.http import JsonResponse
from django.core.files import File
import numpy as np
import time
import cv2
import os
import image_to_midi as im

def FormErrors(*args):
	'''
	Handles form error that are passed back to AJAX calls
	'''
	message = ""
	for f in args:
		if f.errors:
			message = f.errors.as_text()
	return message


def RedirectParams(**kwargs):
	'''
	Used to append url parameters when redirecting users
	'''
	url = kwargs.get("url")
	params = kwargs.get("params")
	response = redirect(url)
	if params:
		query_string = urlencode(params)
		response['Location'] += '?' + query_string
	return response

def Images(*args, **kwargs):
	lat_a = kwargs.get("lat_a")
	long_a = kwargs.get("long_a")
	lat_b = kwargs.get("lat_b")
	long_b = kwargs.get("long_b")
	origin = f'{lat_a},{long_a}'
	destination = f'{lat_b},{long_b}'

	url = "https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&mode=walking&key="enterkey"".format(origin, destination)

	payload={}
	headers = {}
	stepcoords = []

	response = requests.request("GET", url, headers=headers, data=payload)
	response = response.json()

	for step in response['routes'][0]['legs'][0]['steps']:
		lat, lng = step['end_location']['lat'], step['end_location']['lng']
		coord = str(lat) + ',' + str(lng)
		stepcoords.append(coord)

	steplocations = ';'.join(stepcoords)
	print(steplocations)
	return (steplocations)
		

def Directions(*args, **kwargs):
	'''
	Handles directions from Google
	'''

	lat_a = kwargs.get("lat_a")
	long_a = kwargs.get("long_a")
	lat_b = kwargs.get("lat_b")
	long_b = kwargs.get("long_b")
	walking = "WALKING"
	origin = f'{lat_a},{long_a}'
	destination = f'{lat_b},{long_b}'

	result = requests.get(
		'https://maps.googleapis.com/maps/api/directions/json?',
		 params={
		 'origin': origin,
		 'destination': destination,
		 "key": settings.GOOGLE_API_KEY
		 })

	directions = result.json()

	if directions["status"] == "OK":

		routes = directions["routes"][0]["legs"]

		distance = 0
		duration = 0
		route_list = []

		for route in range(len(routes)):

			distance += int(routes[route]["distance"]["value"])
			duration += int(routes[route]["duration"]["value"])

			route_step = {
				'origin': routes[route]["start_address"],
				'destination': routes[route]["end_address"],
				'distance': routes[route]["distance"]["text"],
				'duration': routes[route]["duration"]["text"],

				'steps': [
					[
						s["distance"]["text"],
						s["duration"]["text"],
						s["html_instructions"],

					]
					for s in routes[route]["steps"]]
				}

			
			route_list.append(route_step)
			

	return {
		"origin": origin,
		"destination": destination,
		"distance": f"{round(distance/1000, 2)} Km",
		"duration": format_timespan(duration),
		"route": route_list
		}

def Detect(*args, **kwargs):
	dir = 'routefinder/scraped'
	detecteddir = 'routefinder/detected'
	count = -1

	for f in os.listdir(detecteddir):
		os.remove(os.path.join(detecteddir, f))


	for filename in os.listdir(dir)[:-1]:
		count += 1
		INPUT_FILE = 'routefinder/scraped/{}'.format(filename)
		OUTPUT_FILE='predicted.jpg'
		LABELS_FILE='CCTV/obj.names'
		CONFIG_FILE='CCTV/yolov3-tiny_obj.cfg'
		WEIGHTS_FILE='CCTV/yolov3-tiny_obj_best.weights'
		CONFIDENCE_THRESHOLD=0.2

		LABELS = open(LABELS_FILE).read().strip().split("\n")

		np.random.seed(4)
		COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
			dtype="uint8")


		net = cv2.dnn.readNetFromDarknet(CONFIG_FILE, WEIGHTS_FILE)

		image = cv2.imread(INPUT_FILE)
		(H, W) = image.shape[:2]

		# determine only the *output* layer names that we need from YOLO
		ln = net.getLayerNames()
		ln = [ln[i-1] for i in net.getUnconnectedOutLayers()]


		blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
			swapRB=True, crop=False)
		net.setInput(blob)
		start = time.time()
		layerOutputs = net.forward(ln)
		end = time.time()


		print("[INFO] YOLO took {:.6f} seconds".format(end - start))


		# initialize our lists of detected bounding boxes, confidences, and
		# class IDs, respectively
		boxes = []
		confidences = []
		classIDs = []

		# loop over each of the layer outputs
		for output in layerOutputs:
			# loop over each of the detections
			for detection in output:
				# extract the class ID and confidence (i.e., probability) of
				# the current object detection
				scores = detection[5:]
				classID = np.argmax(scores)
				confidence = scores[classID]

				# filter out weak predictions by ensuring the detected
				# probability is greater than the minimum probability
				if confidence > CONFIDENCE_THRESHOLD:
					# scale the bounding box coordinates back relative to the
					# size of the image, keeping in mind that YOLO actually
					# returns the center (x, y)-coordinates of the bounding
					# box followed by the boxes' width and height
					box = detection[0:4] * np.array([W, H, W, H])
					(centerX, centerY, width, height) = box.astype("int")

					# use the center (x, y)-coordinates to derive the top and
					# and left corner of the bounding box
					x = int(centerX - (width / 2))
					y = int(centerY - (height / 2))

					# update our list of bounding box coordinates, confidences,
					# and class IDs
					boxes.append([x, y, int(width), int(height)])
					confidences.append(float(confidence))
					classIDs.append(classID)
					print(confidence)

					# apply non-maxima suppression to suppress weak, overlapping bounding
					# boxes
					idxs = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD,
						CONFIDENCE_THRESHOLD)

					# ensure at least one detection exists
					if len(idxs) > 0:
						# loop over the indexes we are keeping
						for i in idxs.flatten():
							# extract the bounding box coordinates
							(x, y) = (boxes[i][0], boxes[i][1])
							(w, h) = (boxes[i][2], boxes[i][3])

							color = [int(c) for c in COLORS[classIDs[i]]]

							cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
							text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
							cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
								0.5, color, 2)

					# show the output image

					cv2.imwrite(os.path.join(detecteddir, "gsv_{}.jpg").format(count), image)


def pin(*args, **kwargs):
	dir = 'routefinder/scraped'
	detecteddir = 'routefinder/detected'
	datapath = 'routefinder/scraped/metadata.json'
	results = []
	pincoords = []

	with open(datapath, 'r') as j:
		jsondata = json.loads(j.read())
	
	for foundimage in os.listdir(detecteddir):
		results.append(foundimage)
	
	if results:
		for i in range(len(jsondata)):	
			if jsondata[i]["_file"] in results:
				lat, lng = jsondata[i]["location"]['lat'], jsondata[i]["location"]['lng']
				coord = [float(lat), float(lng)]
				pincoords.append(coord)
	else:
		pincoords = [0]

	return pincoords

	
def audio(*args, **kwargs):
	detecteddir = 'routefinder/detected'
	sounddir = 'routefinder/sound'
	results = []
	for f in os.listdir(sounddir):
		os.remove(os.path.join(sounddir, f))

	for foundimage in os.listdir(detecteddir):
		results.append(foundimage)
    
	if results:
		result = im.image_to_midi("routefinder/detected/{}".format(results[0]), start = 'C1', max_keys = 4, direction = 0, extra_interval = 0.2, rotate = True, line_interval = 1)
		print(result)
		result = result[:14]
		im.write(result, name = 'routefinder/sound/sound.mid')
	


		
