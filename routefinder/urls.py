from django.urls import path
from . import views

app_name = "routefinder"

urlpatterns = [
    path('route', views.route, name="route"),
    path('map', views.map, name="map"),
    path('', views.index, name="index"),
    path('introduction', views.introduction, name="introduction"),
    path('eye', views.eye, name="eye"),
    path('route', views.route, name="route"),
    path('info', views.info, name="info"),
    path('further_research', views.further_research, name="further_research"),
    path('end', views.end, name="end")
]
